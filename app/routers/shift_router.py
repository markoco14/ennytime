from pprint import pprint
from typing import Annotated
import datetime
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks

from sqlalchemy.orm import Session


from app.auth import auth_service
from app.core.database import get_db

from app.schemas import schemas
from app.repositories import shift_repository, shift_type_repository, share_repository, user_repository
from app.services import calendar_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/add-shifts", response_class=HTMLResponse)
def get_add_shifts_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)

    # get the month calendar
    month_calendar = calendar_service.get_month_date_list(
        year=datetime.datetime.now().year,
        month=datetime.datetime.now().month
    )
    # calendar_date_list = []

    calendar_date_list = [(
        date[0],
        date[1],
        date[2],
        calendar_service.DAYS_OF_WEEK[date[3]]
    ) for date in month_calendar]
    # calendar_date_list = list(month_calendar)
    # for date in calendar_date_list:
    #     date[3] = calendar_service.DAYS_OF_WEEK[date[3]]
    # need to be able to navigate months
    # days of month should simply be listed
    # don't need to group by week
    # then each row should have buttons for each shift type
    # click the button, add the shift
    # this will feel way better on the phone

    context = {
        "request": request,
        "user_data": current_user,
        "current_month": datetime.datetime.now().month,
        "month_calendar": calendar_date_list,
    }

    return block_templates.TemplateResponse(
        name="webapp/add-shifts/add-shifts-page.html",
        context=context
    )


@router.get("/shift-table", response_class=HTMLResponse)
def get_shift_table(
    request: Request,
    db: Annotated[Session, Depends(get_db)],

):
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: Session = auth_service.get_session_data(
        db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.User = auth_service.get_current_user(
        db=db, user_id=session_data.user_id)
    shifts = shift_repository.get_user_shifts(db=db, user_id=current_user.id)
    for shift in shifts:
        shift.type = shift_type_repository.get_user_shift_type(
            db=db,
            user_id=current_user.id,
            shift_type_id=shift.type_id
        )
        shift.date = f"{calendar_service.MONTHS[shift.date.month - 1]}  {calendar_service.get_current_day(shift.date.day)}, {shift.date.year}"

    return templates.TemplateResponse(
        request=request,
        name="webapp/profile/shift-table.html",
        context={"request": request, "shifts": shifts}
    )


@router.post("/register-shift", response_class=HTMLResponse)
def schedule_shift(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    shift_type: Annotated[str, Form()],
    date: Annotated[str, Form()],
):
    """Add shift to calendar date"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: Session = auth_service.get_session_data(
        db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.User = auth_service.get_current_user(
        db=db, user_id=session_data.user_id)

    date_segments = date.split("-")

    db_shift = schemas.CreateShift(
        type_id=shift_type,
        user_id=current_user.id,
        date=datetime.datetime(int(date_segments[0]), int(
            date_segments[1]), int(date_segments[2]))
    )

    shift_repository.create_shift(db=db, shift=db_shift)

    db_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=current_user.id)

    # only need to get an array of shifts
    # becauase only for one day, not getting whole calendar
    shifts = []
    for shift in db_shifts:
        if str(shift.date.date()) == date:
            shifts.append(shift._asdict())

    bae_shifts = []
    share = share_repository.get_share_by_guest_id(
        db=db, guest_id=current_user.id)
    if share:
        bae_db_shifts = shift_repository.get_user_shifts_details(
            db=db, user_id=share.owner_id)
        for shift in bae_db_shifts:
            if str(shift.date.date()) == date:
                bae_shifts.append(shift)

    bae_user = user_repository.get_user_by_id(db=db, user_id=share.owner_id)

    context = {
        "request": request,
        "bae_user": bae_user.display_name,
        "current_user": current_user.display_name,
        "date": {
            "date": date,
            "shifts": shifts,
            "day_number": int(date_segments[2]),
            "bae_shifts": bae_shifts,
        },
    }

    return templates.TemplateResponse(
        request=request,
        name="/webapp/home/calendar-card-detail.html",
        context=context,
    )


@router.delete("/delete-shift/{shift_id}", response_class=HTMLResponse | Response)
def delete_shift(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    shift_id: int
):
    shift_repository.delete_user_shift(db=db, shift_id=shift_id)
    return Response(status_code=200)

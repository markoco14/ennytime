"""
Calendar related routes
"""
from typing import Annotated, Optional
from pprint import pprint
import datetime


from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse


from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates
from app.schemas import schemas
from app.repositories import share_repository, shift_repository
from app.repositories import shift_type_repository
from app.services import calendar_service


router = APIRouter()


@router.get("/calendar-card-simple/{date_string}", response_class=HTMLResponse)
def get_simple_calendar_day_card(
        request: Request,
        db: Annotated[Session, Depends(get_db)],
        date_string: str):
    """Get calendar day card"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )
    
    date_segments = date_string.split("-")
    month = date_segments[1]

    session_data: schemas.Session = auth_service.get_session_data(
        db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.AppUser = auth_service.get_current_user(
        db=db, user_id=session_data.user_id)
    date_segments = date_string.split("-")

    db_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=current_user.id)

    # only need to get an array of shifts
    # becauase only for one day, not getting whole calendar
    shifts = []
    for shift in db_shifts:
        if str(shift.date.date()) == date_string:
            shifts.append(shift._asdict())

    bae_shifts = []
    shared_with_me = share_repository.get_share_from_other_user(
        db=db, guest_id=current_user.id)
    if shared_with_me:
        bae_db_shifts = shift_repository.get_user_shifts_details(
            db=db, user_id=shared_with_me.owner_id)
        for shift in bae_db_shifts:
            if str(shift.date.date()) == date_string:
                bae_shifts.append(shift)

    birthdays = []
    if current_user.__dict__["birthday"] and int(month) == current_user.__dict__["birthday"].month:
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.__dict__["birthday"].day
        })
    bae_user = share_repository.get_share_user_with_shifts_by_guest_id(
        db=db, share_user_id=shared_with_me.owner_id)

    if bae_user.birthday and int(month) == bae_user.birthday.month:
        birthdays.append({
            "name": bae_user.display_name,
            "day": bae_user.birthday.day
        })

    context = {
        "request": request,
        "date": {
            "date": date_string,
            "shifts": shifts,
            "day_number": int(date_segments[2]),
            "bae_shifts": bae_shifts,
        },
        "current_user": current_user.display_name,
        "bae_user": bae_user.display_name,
        "birthdays": birthdays
    }

    return templates.TemplateResponse(
        request=request,
        name="/webapp/home/calendar-card-simple.html",
        context=context,
    )



@router.get("/calendar-card-detail/{date_string}", response_class=HTMLResponse)
def get_calendar_card_detailed(
        request: Request,
        db: Annotated[Session, Depends(get_db)],
        date_string: str):
    """Get calendar day card"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: schemas.Session = auth_service.get_session_data(
        db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.AppUser = auth_service.get_current_user(
        db=db, user_id=session_data.user_id)

    date_segments = date_string.split("-")

    # get the user's shifts
    user_shifts_query = text("""
        SELECT etime_shifts.*,
            etime_shift_types.type as type_name,
            etime_shift_types.long_name as long_name,
            etime_shift_types.short_name as short_name
        FROM etime_shifts
        LEFT JOIN etime_shift_types
        ON etime_shifts.type_id = etime_shift_types.id
        WHERE etime_shifts.user_id = :owner_id
        AND DATE(etime_shifts.date) = :date_string
        """)

    user_shifts_result = db.execute(
        user_shifts_query, {"owner_id": current_user.id, "date_string": date_string}).fetchall()

    year = date_segments[0]
    month = date_segments[1]
    day = date_segments[2]
    date = datetime.date(int(year), int(month), int(day))
    written_month = date.strftime("%B %d, %Y")
    day = date.strftime("%A")

    # check if anyone has shared their calendar with the current user
    share_query = text("""
        SELECT etime_shares.*,
            etime_users.display_name as bae_name
        FROM etime_shares
        LEFT JOIN etime_users ON etime_shares.owner_id = etime_users.id 
        WHERE etime_shares.guest_id = :guest_id
    """)

    share_result = db.execute(
        share_query, {"guest_id": current_user.id}).fetchone()

    # organize birthdays
    birthdays = []
    if current_user.__dict__["birthday"] and int(month) == current_user.__dict__["birthday"].month:
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.__dict__["birthday"].day
        })
    bae_user = share_repository.get_share_user_with_shifts_by_guest_id(
        db=db, share_user_id=share_result.owner_id)

    if bae_user.birthday and int(month) == bae_user.birthday.month:
        birthdays.append({
            "name": bae_user.display_name,
            "day": bae_user.birthday.day
        })

    if not share_result:
        context = {
            "request": request,
            "current_user": current_user.display_name,
            "month": month,
            "written_month": written_month,
            "day": day,
            "date": {
                "date": date_string,
                "shifts": user_shifts_result,
                "day_number": int(date_segments[2]),
                "bae_shifts": [],
            },
            "birthdays": birthdays
        }

        return templates.TemplateResponse(
            request=request,
            name="/webapp/home/calendar-card-detail.html",
            context=context,
        )

    # if there is a share, get the sharing user's (bae's) shifts
    shifts_query = text("""
        SELECT etime_shifts.*,
            etime_shift_types.type as type_name,
            etime_shift_types.long_name as long_name,
            etime_shift_types.short_name as short_name
        FROM etime_shifts
        LEFT JOIN etime_shift_types
        ON etime_shifts.type_id = etime_shift_types.id
        WHERE etime_shifts.user_id = :owner_id
        AND DATE(etime_shifts.date) = :date_string
        """)

    shifts_result = db.execute(
        shifts_query, {"owner_id": share_result.owner_id, "date_string": date_string}).fetchall()

    context = {
        "request": request,
        "current_user": current_user.display_name,
        "bae_user": share_result.bae_name,
        "month": month,
        "written_month": written_month,
        "day": day,
        "date": {
            "date": date_string,
            "shifts": user_shifts_result,
            "day_number": int(date_segments[2]),
            "bae_shifts": shifts_result,
        },
        "birthdays": birthdays
    }

    return templates.TemplateResponse(
        request=request,
        name="/webapp/home/calendar-card-detail.html",
        context=context,
    )


@router.get("/add-shift-form/{date_string}", response_class=HTMLResponse)
def get_calendar_day_form(
    request: Request,
    date_string: str,
    db: Annotated[Session, Depends(get_db)],
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """Get calendar day form"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: schemas.Session = auth_service.get_session_data(
        db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.AppUser = auth_service.get_current_user(
        db=db, user_id=session_data.user_id)

    shift_types = shift_type_repository.list_user_shift_types(
        db=db,
        user_id=current_user.id)
    current_month = calendar_service.get_current_month(month)
    current_year = calendar_service.get_current_year(year)
    year_string = date_string.split("-")[0]
    month_string = date_string.split("-")[1]
    day_string = date_string.split("-")[2]

    # TODO: Get the day of the week

    # TODO: Get the current user shifts for this day
    query = text("""
        SELECT
            etime_shifts.*
        FROM etime_shifts
        WHERE etime_shifts.user_id = :user_id
        AND etime_shifts.date = :date_string
        ORDER BY etime_shifts.date
    """)

    result = db.execute(
        query,
        {"user_id": current_user.id,
         "date_string": date_string
         }
    ).fetchall()

    user_shifts = []
    for row in result:
        user_shifts.append(row._asdict())
    year = date_string.split("-")[0]
    month = date_string.split("-")[1]
    day = date_string.split("-")[2]
    date = datetime.date(int(year), int(month), int(day))
    month = date.strftime("%B %d, %Y")
    day = date.strftime("%A")

    date_dict = {
        "date_string": f"{year_string}-{month_string}-{day_string}",
        "day_of_week": str(calendar_service.get_weekday(date_string)),
        "shifts": user_shifts,
    }

    context = {
        "request": request,
        "shift_types": shift_types,
        "day_number": int(date_string.split("-")[2]),
        "current_month": current_month,
        "current_year": current_year,
        "date_string": date_string,
        "readable_month": month,
        "date": date_dict,
    }

    return templates.TemplateResponse(
        request=request,
        name="/webapp/home/add-shift-form.html",
        context=context
    )


"""
Calendar related routes
"""
from typing import Annotated, Optional
from pprint import pprint
import datetime


from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse


from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates, block_templates
from app.models.share_model import DbShare
from app.models.user_model import DBUser
from app.schemas import schemas
from app.repositories import share_repository, shift_repository
from app.repositories import shift_type_repository
from app.services import calendar_service, calendar_shift_service, chat_service


router = APIRouter()

@router.get("/calendar/{year}/{month}", response_class=HTMLResponse)
def get_calendar_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    month: Optional[int] = None,
    year: Optional[int] = None,
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response
    
    current_time = datetime.datetime.now()
    selected_year = year or current_time.year
    selected_month = month or current_time.month
    selected_month_name = calendar_service.MONTHS[selected_month - 1]

    # handle all birthday logic
    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=selected_month):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
        })

    # get user who shares their calendar with current user
    # find the DbShare where current user id is the receiver_id 
    bae_user = db.query(DBUser).join(DbShare, DBUser.id == DbShare.sender_id).filter(
        DbShare.receiver_id == current_user.id).first()

    if bae_user:
        if bae_user.has_birthday() and bae_user.birthday_in_current_month(current_month=selected_month):
            birthdays.append({
                "name": bae_user.display_name,
                "day": bae_user.birthday.day
            })

    # get previous and next month names for month navigation
    prev_month_name, next_month_name = calendar_service.get_prev_and_next_month_names(
        current_month=selected_month)

    month_calendar = calendar_service.get_month_calendar(
        year=selected_year, 
        month=selected_month
        )

    month_calendar_dict = dict((str(day), {"date": str(
        day), "day_number": day.day, "month_number": day.month, "shifts": [], "bae_shifts": []}) for day in month_calendar)

    
    # gathering user ids to query shift table and get shifts for both users at once
    user_ids = [current_user.id]
    if bae_user:
        user_ids.append(bae_user.id)

    # get the start and end of the month for query filters
    start_of_month = calendar_service.get_start_of_month(year=selected_year, month=selected_month)
    end_of_month = calendar_service.get_end_of_month(year=selected_year, month=selected_month)

    # get shifts for current user and bae user
    all_shifts = calendar_shift_service.get_month_shift_info_for_users(
        db=db,
        user_ids=user_ids,
        start_of_month=start_of_month,
        end_of_month=end_of_month
        )
    
    # update the calendar dictionary with sorted shifts
    month_calendar_dict = calendar_shift_service.sort_shifts_by_user(all_shifts=all_shifts, month_calendar_dict=month_calendar_dict, current_user=current_user)

    context = {
        "request": request,
        "current_user": current_user,
        "birthdays": birthdays,
        "selected_month": selected_month,
        "selected_month_name": selected_month_name,
        "selected_year": selected_year,
        "prev_month_name": prev_month_name,
        "next_month_name": next_month_name,
        "month_calendar": list(month_calendar_dict.values()),
        "days_of_week": calendar_service.DAYS_OF_WEEK,
    }

    if "hx-request" in request.headers:
        response = templates.TemplateResponse(
            name="calendar/fragments/calendar-oob.html",
            context=context,
        )
        return response

    # get chatroom id to link directly from the chat icon
    # get unread message count so chat icon can display the count on page load
    user_chat_data = chat_service.get_user_chat_data(
        db=db,
        current_user_id=current_user.id
    )

    context.update({"chat_data": user_chat_data})  
    response = templates.TemplateResponse(
        name="calendar/index.html",
        context=context,
    )

    return response

@router.get("/calendar-card-simple/{date_string}", response_class=HTMLResponse)
def get_simple_calendar_day_card(
        request: Request,
        db: Annotated[Session, Depends(get_db)],
        date_string: str,
        current_user=Depends(auth_service.user_dependency)
):
    """Get calendar day card"""
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    year_number, month_number, day_number = calendar_service.extract_date_string_numbers(
        date_string=date_string)

    db_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=current_user.id)

    # only need to get an array of shifts
    # becauase only for one day, not getting whole calendar
    shifts = []
    for shift in db_shifts:
        if str(shift.date.date()) == date_string:
            shifts.append(shift._asdict())

    bae_shifts = []
    shared_with_me = share_repository.get_share_by_receiver_id(
        db=db, receiver_id=current_user.id)
    if shared_with_me:
        bae_db_shifts = shift_repository.get_user_shifts_details(
            db=db, user_id=shared_with_me.sender_id)
        for shift in bae_db_shifts:
            if str(shift.date.date()) == date_string:
                bae_shifts.append(shift)

    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=month_number):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
        })

    if shared_with_me:
        bae_user = share_repository.get_share_user_with_shifts_by_receiver_id(
            db=db, share_user_id=shared_with_me.sender_id)

        if bae_user.has_birthday() and bae_user.birthday_in_current_month(current_month=month_number):
            birthdays.append({
                "name": bae_user.display_name,
                "day": bae_user.birthday.day
            })

    context = {
        "request": request,
        "date": {
            "date": date_string,
            "shifts": shifts,
            "day_number": day_number,
            "bae_shifts": bae_shifts,
        },
        "selected_month": month_number,
        "current_user": current_user,
        "birthdays": birthdays
    }

    return templates.TemplateResponse(
        request=request,
        name="/calendar/calendar-card-simple.html",
        context=context,
    )


@router.get("/calendar-card-detail/{date_string}", response_class=HTMLResponse)
def get_calendar_card_detailed(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    date_string: str,
    current_user=Depends(auth_service.user_dependency)
):
    """Get calendar day card"""
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    # get the user's shifts
    user_shifts_query = text("""
        SELECT etime_shifts.*,
            etime_shift_types.long_name as long_name,
            etime_shift_types.short_name as short_name
        FROM etime_shifts
        LEFT JOIN etime_shift_types
        ON etime_shifts.type_id = etime_shift_types.id
        WHERE etime_shifts.user_id = :sender_id
        AND DATE(etime_shifts.date) = :date_string
        """)

    user_shifts_result = db.execute(
        user_shifts_query, {"sender_id": current_user.id, "date_string": date_string}).fetchall()

    year_number, month_number, day_number = calendar_service.extract_date_string_numbers(
        date_string)
    date = datetime.date(year_number, month_number, day_number)
    written_month = date.strftime("%B %d, %Y")
    written_day = date.strftime("%A")

    # check if anyone has shared their calendar with the current user
    share_query = text("""
        SELECT etime_shares.*,
            etime_users.display_name as bae_name
        FROM etime_shares
        LEFT JOIN etime_users ON etime_shares.sender_id = etime_users.id 
        WHERE etime_shares.receiver_id = :receiver_id
    """)

    share_result = db.execute(
        share_query, {"receiver_id": current_user.id}).fetchone()

    # organize birthdays
    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=month_number):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
        })
    if share_result:
        bae_user = share_repository.get_share_user_with_shifts_by_receiver_id(
            db=db, share_user_id=share_result.sender_id)

        if bae_user.has_birthday() and bae_user.birthday_in_current_month(current_month=month_number):
            birthdays.append({
                "name": bae_user.display_name,
                "day": bae_user.birthday.day
            })

    if not share_result:
        context = {
            "request": request,
            "current_user": current_user,
            "month": month_number,
            "written_month": written_month,
            "written_day": written_day,
            "date": {
                "date": date_string,
                "shifts": user_shifts_result,
                "day_number": day_number,
                "bae_shifts": [],
            },
            "selected_month": month_number,
            "birthdays": birthdays
        }

        return templates.TemplateResponse(
            request=request,
            name="/calendar/calendar-card-detail.html",
            context=context,
        )

    # if there is a share, get the sharing user's (bae's) shifts
    shifts_query = text("""
        SELECT etime_shifts.*,
            etime_shift_types.long_name as long_name,
            etime_shift_types.short_name as short_name
        FROM etime_shifts
        LEFT JOIN etime_shift_types
        ON etime_shifts.type_id = etime_shift_types.id
        WHERE etime_shifts.user_id = :sender_id
        AND DATE(etime_shifts.date) = :date_string
        """)

    shifts_result = db.execute(
        shifts_query, {"sender_id": share_result.sender_id, "date_string": date_string}).fetchall()

    context = {
        "request": request,
        "current_user": current_user,
        "bae_user": bae_user,
        "month": month_number,
        "written_month": written_month,
        "written_day": written_day,
        "date": {
            "date": date_string,
            "shifts": user_shifts_result,
            "day_number": day_number,
            "bae_shifts": shifts_result,
        },
        "selected_month": month_number,
        "birthdays": birthdays
    }

    return templates.TemplateResponse(
        request=request,
        name="/calendar/calendar-card-detail.html",
        context=context,
    )


@router.get("/calendar/card/detail/{date_string}", response_class=HTMLResponse)
def get_calendar_card_detailed(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    date_string: str,
    current_user=Depends(auth_service.user_dependency)
):
    """Get calendar day card"""
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    # get the user's shifts
    user_shifts_query = text("""
        SELECT etime_shifts.*,
            etime_shift_types.long_name as long_name,
            etime_shift_types.short_name as short_name
        FROM etime_shifts
        LEFT JOIN etime_shift_types
        ON etime_shifts.type_id = etime_shift_types.id
        WHERE etime_shifts.user_id = :sender_id
        AND DATE(etime_shifts.date) = :date_string
        """)

    user_shifts_result = db.execute(
        user_shifts_query, {"sender_id": current_user.id, "date_string": date_string}).fetchall()

    year_number, month_number, day_number = calendar_service.extract_date_string_numbers(
        date_string)
    date = datetime.date(year_number, month_number, day_number)
    written_month = date.strftime("%B %d, %Y")
    written_day = date.strftime("%A")

    # check if anyone has shared their calendar with the current user
    share_query = text("""
        SELECT etime_shares.*,
            etime_users.display_name as bae_name
        FROM etime_shares
        LEFT JOIN etime_users ON etime_shares.sender_id = etime_users.id 
        WHERE etime_shares.receiver_id = :receiver_id
    """)

    share_result = db.execute(
        share_query, {"receiver_id": current_user.id}).fetchone()

    # organize birthdays
    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=month_number):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
        })
    if share_result:
        bae_user = share_repository.get_share_user_with_shifts_by_receiver_id(
            db=db, share_user_id=share_result.sender_id)

        if bae_user.has_birthday() and bae_user.birthday_in_current_month(current_month=month_number):
            birthdays.append({
                "name": bae_user.display_name,
                "day": bae_user.birthday.day
            })

    if not share_result:
        context = {
            "request": request,
            "current_user": current_user,
            "month": month_number,
            "written_month": written_month,
            "written_day": written_day,
            "date": {
                "date": date_string,
                "shifts": user_shifts_result,
                "day_number": day_number,
                "bae_shifts": [],
            },
            "birthdays": birthdays
        }

        return templates.TemplateResponse(
            request=request,
            name="/calendar/fragments/detail-view.html",
            context=context,
        )

    # if there is a share, get the sharing user's (bae's) shifts
    shifts_query = text("""
        SELECT etime_shifts.*,
            etime_shift_types.long_name as long_name,
            etime_shift_types.short_name as short_name
        FROM etime_shifts
        LEFT JOIN etime_shift_types
        ON etime_shifts.type_id = etime_shift_types.id
        WHERE etime_shifts.user_id = :sender_id
        AND DATE(etime_shifts.date) = :date_string
        """)

    shifts_result = db.execute(
        shifts_query, {"sender_id": share_result.sender_id, "date_string": date_string}).fetchall()

    context = {
        "request": request,
        "current_user": current_user,
        "bae_user": bae_user,
        "month": month_number,
        "written_month": written_month,
        "written_day": written_day,
        "date": {
            "date": date_string,
            "shifts": user_shifts_result,
            "day_number": day_number,
            "bae_shifts": shifts_result,
        },
        "birthdays": birthdays
    }

    return templates.TemplateResponse(
        request=request,
        name="/calendar/fragments/detail-view.html",
        context=context,
    )


@router.get("/calendar/card/{date_string}/edit")
def get_calendar_card_edit(
    request: Request,
    date_string: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
):
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response
    db_shift_types = shift_type_repository.list_user_shift_types(db=db, user_id=current_user.id)

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

    context= {
        "request": request,
        "current_user": current_user,
        "shifts": user_shifts,
        "shift_types": db_shift_types,
        "date_string": date_string
    }

    return templates.TemplateResponse(
        name="/calendar/fragments/edit-view.html",
        context=context
    )


@router.post("/calendar/card/{date_string}/edit/{shift_type_id}")
def get_calendar_card_edit(
    request: Request,
    date_string: str,
    shift_type_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
):
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response
     # check if shift already exists
    # if exists delete, user will already have clicked a confirm on the frontend

    date_segments = date_string.split("-")
    db_shift = schemas.CreateShift(
        type_id=shift_type_id,
        user_id=current_user.id,
        date=datetime.datetime(int(date_segments[0]), int(
            date_segments[1]), int(date_segments[2]))
    )

    new_shift = shift_repository.create_shift(db=db, shift=db_shift)

    shift_type = shift_type_repository.get_user_shift_type(
        db=db, user_id=current_user.id, shift_type_id=shift_type_id)

    context = {
        "current_user": current_user,
        "request": request,
        "date_string": date_string,
        "shift_type": shift_type
    }

    return block_templates.TemplateResponse(
        name="/calendar/fragments/edit-view.html",
        context=context,
        block_name="shift_exists_button"
    )



@router.delete("/calendar/card/{date_string}/edit/{shift_type_id}", response_class=HTMLResponse)
async def delete_shift_for_date(
    request: Request,
    date_string: str,
    shift_type_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
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

    # check if shift already exists
    # if exists delete, user will already have clicked a confirm on the frontend
    date_segments = date_string.split("-")
    date_object = datetime.datetime(
        int(date_segments[0]), int(date_segments[1]), int(date_segments[2]))

    existing_shift = shift_repository.get_user_shift(
        db=db, user_id=current_user.id, type_id=shift_type_id, date_object=date_object)

    if not existing_shift:
        return Response(status_code=404)

    shift_repository.delete_user_shift(db=db, shift_id=existing_shift.id)
    shift_type = shift_type_repository.get_user_shift_type(
        db=db, user_id=current_user.id, shift_type_id=shift_type_id)
    context = {
        "current_user": current_user,
        "request": request,
        "date_string": date_string,
        "shift_type": shift_type
    }

    return block_templates.TemplateResponse(
        name="/calendar/fragments/edit-view.html",
        context=context,
        block_name="no_shift_button"
    )

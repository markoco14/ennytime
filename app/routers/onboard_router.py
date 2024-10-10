import datetime

from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates
from app.repositories import shift_type_repository
from app.schemas import schemas
from app.models.user_model import DBUser
from app.services import calendar_service

router = APIRouter(prefix="/quick-setup")

@router.get("/shifts", response_class=HTMLResponse)
def get_quick_setup_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    db_shift_types = shift_type_repository.list_user_shift_types(db=db, user_id=current_user.id)
    context= {
        "request": request,
        "current_user": current_user,
        "message_count": 0,
        "shift_types": db_shift_types,
        "shift_name": ""
    }

    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="/quick-setup/shifts/fragments/shift-content-oob.html",
            context=context)
        response.headers["HX-Push-Url"] = "/quick-setup/shifts"

        return response

    return templates.TemplateResponse(name="/quick-setup/shifts/index.html", context=context)

@router.get("/validate-shift")
def validate_shift_name(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    shift_name: str = ""
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    context = {          
        "request": request,
        "shift_name": shift_name,
    }
    
    if shift_name == "":
        return templates.TemplateResponse(
            request=request,
            name="quick-setup/shifts/fragments/submit-button-disabled.html",
            context=context
        )

    return templates.TemplateResponse(
        request=request,
        name="quick-setup/shifts/fragments/submit-button-enabled.html",
        context=context
    )

@router.post("/shifts", response_class=HTMLResponse)
def store_first_shift(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    shift_name: Annotated[str, Form()],
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    current_time = datetime.datetime.now()
    year = current_time.year
    month = current_time.month

    month_calendar = calendar_service.get_month_date_list(
        year=year,
        month=month
    )

    # calendar_date_list is a list of dictionaries
    # the keys are date_strings to make matching shifts easier
    # ie; "2021-09-01": {"more keys": "more values"}
    calendar_date_list = {}

    # because month calendar year/month/day are numbers
    # numbers less than 10 don't have preceeding 0's to match the formatting of
    # the date strings, need to add 0's to the front of the numbers
    for date in month_calendar:
        year_string = f"{date[0]}"
        month_string = f"{date[1]}"
        day_string = f"{date[2]}"
        if date[1] < 10:
            month_string = f"0{date[1]}"
        if date[2] < 10:
            day_string = f"0{date[2]}"
        
        date_object = datetime.date(year=date[0], month=date[1], day=date[2])
        date_dict = {
            f"{year_string}-{month_string}-{day_string}": {
                "date_string": f"{date_object.year}-{month_string}-{day_string}",
                "day_of_week": str(calendar_service.Weekday(date[3])),
                "date_object": date_object
            }
        }
        if date[1] == month:
            calendar_date_list.update(date_dict)
    long_name_split = shift_name.split(" ")
    short_name = ""
    for part in long_name_split:
        short_name += part[0].upper()
    # get new shift type data ready
    new_shift_type = schemas.CreateShiftType(
        long_name=shift_name,
        short_name=short_name,
        user_id=current_user.id
    )

    # create new shift type or return an error
    shift_type_repository.create_shift_type(
        db=db,
        shift_type=new_shift_type
    )
    
    shift_types = shift_type_repository.list_user_shift_types(db=db, user_id=current_user.id)
    # get the start and end of the month for query filters
    start_of_month = datetime.datetime(year, month, 1)
    end_of_month = datetime.datetime(
        year, month + 1, 1) + datetime.timedelta(seconds=-1)
    
    query = text("""
        SELECT
            etime_shifts.*
        FROM etime_shifts
        WHERE etime_shifts.user_id = :user_id
        AND etime_shifts.date >= :start_of_month
        AND etime_shifts.date <= :end_of_month
        ORDER BY etime_shifts.date
    """)

    result = db.execute(
        query,
        {"user_id": current_user.id,
         "start_of_month": start_of_month,
         "end_of_month": end_of_month}
    ).fetchall()
    user_shifts = []
    for row in result:
        user_shifts.append(row._asdict())

    # here is the problem
    # overwriting the previous shift when there are 2
    # only 1 being packed and sent
    for shift in user_shifts:
        key_to_find = f"{shift['date'].date()}"
        if key_to_find in calendar_date_list:
            if not calendar_date_list[f"{key_to_find}"].get("shifts"):
                calendar_date_list[f"{key_to_find}"]["shifts"] = []

            calendar_date_list[f"{key_to_find}"]["shifts"].append(shift)

    context= {
        "request": request,
        "current_user": current_user,
        "month_calendar": calendar_date_list,
        "shift_types": shift_types,
        "user_shifts": user_shifts
    }
    
    response = templates.TemplateResponse(
        name="/quick-setup/shifts/fragments/shift-content.html",                               
        context=context
        )

    return response


@router.get("/schedule")
def get_schedule_first_shift_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    current_time = datetime.datetime.now()
    year = current_time.year
    month = current_time.month

    month_calendar = calendar_service.get_month_date_list(
        year=year,
        month=month
    )

    # calendar_date_list is a list of dictionaries
    # the keys are date_strings to make matching shifts easier
    # ie; "2021-09-01": {"more keys": "more values"}
    calendar_date_list = {}

    # because month calendar year/month/day are numbers
    # numbers less than 10 don't have preceeding 0's to match the formatting of
    # the date strings, need to add 0's to the front of the numbers
    for date in month_calendar:
        year_string = f"{date[0]}"
        month_string = f"{date[1]}"
        day_string = f"{date[2]}"
        if date[1] < 10:
            month_string = f"0{date[1]}"
        if date[2] < 10:
            day_string = f"0{date[2]}"
        
        date_object = datetime.date(year=date[0], month=date[1], day=date[2])
        date_dict = {
            f"{year_string}-{month_string}-{day_string}": {
                "date_string": f"{date_object.year}-{month_string}-{day_string}",
                "day_of_week": str(calendar_service.Weekday(date[3])),
                "date_object": date_object
            }
        }
        if date[1] == month:
            calendar_date_list.update(date_dict)
    shift_types = shift_type_repository.list_user_shift_types(db=db, user_id=current_user.id)

    # get the start and end of the month for query filters
    start_of_month = datetime.datetime(year, month, 1)
    end_of_month = datetime.datetime(
        year, month + 1, 1) + datetime.timedelta(seconds=-1)
    
    query = text("""
        SELECT
            etime_shifts.*
        FROM etime_shifts
        WHERE etime_shifts.user_id = :user_id
        AND etime_shifts.date >= :start_of_month
        AND etime_shifts.date <= :end_of_month
        ORDER BY etime_shifts.date
    """)

    result = db.execute(
        query,
        {"user_id": current_user.id,
         "start_of_month": start_of_month,
         "end_of_month": end_of_month}
    ).fetchall()
    user_shifts = []
    for row in result:
        user_shifts.append(row._asdict())

    # here is the problem
    # overwriting the previous shift when there are 2
    # only 1 being packed and sent
    for shift in user_shifts:
        key_to_find = f"{shift['date'].date()}"
        if key_to_find in calendar_date_list:
            if not calendar_date_list[f"{key_to_find}"].get("shifts"):
                calendar_date_list[f"{key_to_find}"]["shifts"] = []

            calendar_date_list[f"{key_to_find}"]["shifts"].append(shift)
    context= {
        "request": request,
        "current_user": current_user,
        "month_calendar": calendar_date_list,
        "shift_types": shift_types,
        "user_shifts": user_shifts,
    }

    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="/quick-setup/scheduling/fragments/schedule-content-oob.html",                               
            context=context
            )
        response.headers["HX-Push-Url"] = "/quick-setup/schedule"
        return response
    
    context.update({"message_count": 0})

    response = templates.TemplateResponse(
        name="/quick-setup/scheduling/index.html",
        context=context
    )
    return response

@router.get("/username", response_class=HTMLResponse)
def get_quick_setup_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    context={
        "request": request,
        "current_user": current_user
        }
    
    username = current_user.username or ""
    context.update({"username": username})
    
    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="/quick-setup/username/fragments/username-content-oob.html",
            context=context
        )
        response.headers["HX-Push-Url"] = "/quick-setup/username"

        return response
    
    context.update({"message_count": 0})

    response = templates.TemplateResponse(
        name="/quick-setup/username/index.html",
        context=context
    )

    return response


@router.put("/username/{user_id}")
def update_username_widget(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    app_username: Annotated[str, Form()] = None,
    current_user=Depends(auth_service.user_dependency)
):
    """Returns HTML to let the user edit their username"""
    if not current_user:
        response = RedirectResponse(url="/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if current_user.id != user_id:
        return Response(status_code=403)
    
    if not app_username:
        return Response(status_code=400)

    current_user.username = app_username
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    context = {
        "request": request,
        "current_user": current_user
    }

    if request.headers.get("HX-Request"):
        display_name = current_user.display_name or ""
        context.update({"display_name": display_name})
        response = templates.TemplateResponse(
            name="/quick-setup/display-name/fragments/display-name-content-oob.html",
            context=context
            )
        
        return response

    response = Response(status_code=303)
    response.headers["HX-Redirect"] = "/quick-setup/display-name"
    
    return response


@router.get("/username-unique")
def onboarding_validate_username(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    app_username: str = "",
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    context = {
        "request": request,
        "user": current_user,
    }

    if app_username == "":
        context.update({"error": True})
        if current_user.username:
            context.update({
                "username": current_user.username
            })
        else:
            context.update({
                "username": ""
            })


        return templates.TemplateResponse(
            request=request,
            name="quick-setup/username/fragments/input-errors.html",
            context=context
        )

    if app_username == current_user.username:
        context.update({
            "username": app_username,
            "error": True
        })

        return templates.TemplateResponse(
            request=request,
            name="quick-setup/username/fragments/input-errors.html",
            context=context
        )

    db_username = db.query(DBUser).filter(
        DBUser.username == app_username).first()

    if not db_username:
        username_taken = False
    else:
        username_taken = True

    context.update({          
        "username": app_username,
        "error": username_taken
    })

    return templates.TemplateResponse(
        request=request,
        name="quick-setup/username/fragments/input-errors.html",
        context=context
    )

@router.get("/display-name")
def get_display_name_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    display_name = current_user.display_name or ""
    
    context={
        "request": request,
        "current_user": current_user,
        "display_name": display_name
        }
    
    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="/quick-setup/display-name/fragments/display-name-content-oob.html",
            context=context
        )
        response.headers["HX-Push-Url"] = "/quick-setup/display-name"

        return response
        
    response = templates.TemplateResponse(
        name="/quick-setup/display-name/index.html",
        context=context
    )

    return response

@router.get("/validate-display-name")
def onboarding_validate_username(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    display_name: str = "",
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    context = {          
        "request": request,
        "display_name": display_name,
    }
    
    if display_name == "":
        return templates.TemplateResponse(
            request=request,
            name="quick-setup/display-name/submit-disabled-oob.html",
            context=context
        )

    return templates.TemplateResponse(
        request=request,
        name="quick-setup/display-name/submit-enabled-oob.html",
        context=context
    )


@router.put("/display-name/{user_id}")
def update_display_name_widget(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    display_name: Annotated[str, Form()] = None,
):
    """Returns HTML to let the user edit their display name"""
    if not current_user:
        response = RedirectResponse(url="/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if current_user.id != user_id:
        return Response(status_code=403)
    
    if not display_name:
        return Response(status_code=400)

    current_user.display_name = display_name
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    response = Response(status_code=303)
    response.headers["HX-Redirect"] = "/"
    
    return response
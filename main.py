"""Main file to hold app and api routes"""
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from mangum import Mangum
from sqlalchemy.orm import Session

from app.auth import auth_router, auth_service
from app.core.database import get_db
from app.repositories import share_repository, shift_repository, shift_type_repository
from app.repositories import user_repository
from app.routers import admin_router, calendar_router, share_router, shift_router, shift_type_router, user_router
from app.schemas import schemas
from app.services import calendar_service

app = FastAPI()
app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(user_router.router)
app.include_router(shift_type_router.router)
app.include_router(shift_router.router)
app.include_router(calendar_router.router)
app.include_router(share_router.router)

templates = Jinja2Templates(directory="templates")

handler = Mangum(app)

@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    month: Optional[int] = None,
    year: Optional[int] = None,
    ):
    """Index page"""
    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
            )
        response.delete_cookie("session-id")
    
        return response

    current_month = calendar_service.get_current_month(month)
    current_year = calendar_service.get_current_year(year)

    month_calendar = calendar_service.get_month_calendar(current_year, current_month)
    
    month_calendar_dict = dict((str(day), {"date": str(day), "day_number": day.day, "month_number": day.month, "shifts": [], "bae_shifts": []}) for day in month_calendar)
    
    db_shifts = shift_repository.get_user_shifts(db=db, user_id=current_user.id)
    
    # get users detailed shift info for matching dates
    for shift in db_shifts:
        shift_date = str(shift.date.date())
        if month_calendar_dict.get(shift_date):
            db_shift_type = shift_type_repository.get_user_shift_type(db=db, user_id=current_user.id, shift_type_id=shift.type_id)
            # month_calendar_dict[shift_date]['shift_type_id'] = shift.type_id
            # month_calendar_dict[shift_date]['shift_type'] = db_shift_type
            month_calendar_dict[shift_date]['shifts'].append(db_shift_type)
        
    # just get a single share
    # because a user can only share with 1 person for now
    # and also be shared with 1 person
    share = share_repository.get_share_by_guest_id(db=db, guest_id=current_user.id)
    if share:
        bae_shifts = shift_repository.get_user_shifts(db=db, user_id=share.owner_id)
        for shift in bae_shifts:
            shift_date = str(shift.date.date())
            if month_calendar_dict.get(shift_date):
                db_shift_type = shift_type_repository.get_user_shift_type(db=db, user_id=share.owner_id, shift_type_id=shift.type_id)
                month_calendar_dict[shift_date]['bae_shifts'].append(db_shift_type)


    context = {
        "month_number": month,
        "request": request,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "current_year": current_year,
        "current_month_number": current_month,
        "current_month": calendar_service.MONTHS[current_month - 1],
        "month_calendar": list(month_calendar_dict.values()),
    }

    response = templates.TemplateResponse(
        request=request,
        name="webapp/home/app-home.html",
        context=context,
        )
    
    
    
    return response


@app.get("/signin", response_class=HTMLResponse)
def get_signin_page(request: Request):
    """Go to the sign in page"""
    return templates.TemplateResponse(
        request=request,
        name="website/signin.html",
        )

@app.get("/signup", response_class=HTMLResponse)
def get_signup_page(request: Request):
    """Go to the sign up page"""
    return templates.TemplateResponse(
        request=request,
        name="website/signup.html",
    )


@app.post("/search", response_class=HTMLResponse)
def search_users_to_share(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    search_display_name: Annotated[str, Form()] = ""
    ):
    """ Returns a list of users that match the search string. """
    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
            )
        response.delete_cookie("session-id")
    
        return response
    
    if search_display_name == "":
        return templates.TemplateResponse(
            request=request,
            name="webapp/profile/search-results.html",
            context={"request": request, "matching_users": []}
        )
    
    search_display_name_lower = search_display_name.lower()

    matching_users = user_repository.list_users_by_display_name(db=db, current_user_id=current_user.id, display_name=search_display_name_lower)
        
    context = {"request": request, "matching_users": matching_users}

    return templates.TemplateResponse(
        request=request,
        name="webapp/profile/search-results.html",
        context=context
    )


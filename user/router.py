
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from auth import auth_service
from repositories import shift_type_repository
from schemas import Session, User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/profile", response_class=HTMLResponse | Response)
def get_profile_page(request: Request):
    """Profile page"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: Session = auth_service.get_session_data(request.cookies.get("session-id"))
    
    current_user: User = auth_service.get_current_user(user_id=session_data.user_id)

    shift_types = shift_type_repository.list_user_shift_types(
        user_id=current_user.id)
    
    context = {
        "request": request,
        "shift_types": shift_types,
        "user": current_user,
    }

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context=context
        )

@router.get("/contact/{user_id}", response_class=HTMLResponse | Response)
def get_display_name_widget(request: Request, user_id: int):
	if not auth_service.get_session_cookie(request.cookies):
		return templates.TemplateResponse(
			request=request,
			name="landing-page.html",
			headers={"HX-Redirect": "/"},
		)

	session_data: Session = auth_service.get_session_data(request.cookies.get("session-id"))
	
	current_user: User = auth_service.get_current_user(user_id=session_data.user_id)

	if current_user.id != user_id:
		return Response(status_code=403)
	
	context = {
		"request": request,
		"user": current_user,
	}
	return templates.TemplateResponse(
		request=request,
		name="/contact/display-name.html",
		context=context
		)

@router.get("/contact/{user_id}/edit", response_class=HTMLResponse | Response)
def get_edit_display_name_widget(request: Request, user_id: int):
	"""Edit contact page"""
	print(user_id)
	if not auth_service.get_session_cookie(request.cookies):
		return templates.TemplateResponse(
			request=request,
			name="landing-page.html",
			headers={"HX-Redirect": "/"},
		)

	session_data: Session = auth_service.get_session_data(request.cookies.get("session-id"))
	
	current_user: User = auth_service.get_current_user(user_id=session_data.user_id)

	if current_user.id != user_id:
		return Response(status_code=403)

	context = {
		"request": request,
		"user": current_user,
	}

	return templates.TemplateResponse(
		request=request,
		name="/contact/display-name-edit.html",
		context=context
		)
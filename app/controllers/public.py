
import datetime
from typing import Optional
from fastapi import Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.auth import auth_service
from app.core.template_utils import templates


def index(
    request: Request,
    response: Response,
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user=Depends(auth_service.user_dependency)
):
    """Index page"""
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response
    
    current_time = datetime.datetime.now()
    selected_year = year or current_time.year
    selected_month = month or current_time.month
    
    # HX-Redirect required for hx-request
    if "hx-request" in request.headers:
        response = Response(status_code=303)
        response.headers["HX-Redirect"] = f"/calendar/{selected_year}/{selected_month}"
        return response
    
    # Can use FastAPI Redirect with standard http request
    return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")
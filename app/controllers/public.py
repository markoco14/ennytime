import datetime
from typing import Annotated, Optional

from fastapi import Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.core.template_utils import templates
from app.dependencies import requires_guest
from app.models.user import User

def index(
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(requires_guest)],
    month: Optional[int] = None,
    year: Optional[int] = None,
):
    """Index page"""
    current_time = datetime.datetime.now()
    selected_year = year or current_time.year
    selected_month = month or current_time.month
    
    if current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/calendar/{selected_year}/{selected_month}"})
        else:
            return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")

    response = templates.TemplateResponse(
        request=request,
        name="website/web-home.html"
    )

    return response

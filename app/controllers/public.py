import datetime
from typing import Optional

from fastapi import Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.core.template_utils import templates
from app.dependencies import requires_guest

def index(
    request: Request,
    response: Response,
    month: Optional[int] = None,
    year: Optional[int] = None,
    lite_user=Depends(requires_guest)
):
    """Index page"""
    current_time = datetime.datetime.now()
    selected_year = year or current_time.year
    selected_month = month or current_time.month
    
    if lite_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/calendar/{selected_year}/{selected_month}"})
        else:
            return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")

    response = templates.TemplateResponse(
        request=request,
        name="website/web-home.html"
    )

    return response

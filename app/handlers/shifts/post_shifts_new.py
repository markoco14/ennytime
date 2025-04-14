import re

from fastapi import Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.template_utils import templates
from app.models.user_model import DBUser
from app.schemas import schemas
from app.repositories import shift_type_repository


def handle_post_shifts_new(request: Request, current_user: DBUser, shift_name: str, date_string: str, db: Session):
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response
    
    # clean up shift name
    cleaned_shift_name = shift_name.strip()
    space_finder_regex = re.compile(r"\s+")
    cleaned_shift_name = re.sub(space_finder_regex, ' ', cleaned_shift_name)
   
    # create short name
    long_name_split = cleaned_shift_name.split(" ")
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
    
    # TODO: change this to return single shift type and animate it into the list
    # get the new shift type list
    shift_types = shift_type_repository.list_user_shift_types(
        db=db,
        user_id=current_user.id
    )

    context = {
        "request": request,
        "shift_types": shift_types,
    }

    hx_current_url = request.headers.get("hx-current-url") or None
    from_setup_page = "/shifts/setup" in hx_current_url
    from_new_page = "/shifts/new" in hx_current_url
    if from_new_page or from_setup_page:
        response = Response(status_code=303)
        response.headers["HX-Redirect"] = "/shifts"

        return response
    
    context.update({"date_string": date_string})
    response = templates.TemplateResponse(
        name="/calendar/fragments/edit-view.html",
        context=context
        )
    
    return response
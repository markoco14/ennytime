
from fastapi import Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.models.user_model import DBUser
from app.repositories import shift_type_repository


def handle_delete_shift(request: Request, current_user: DBUser, shift_type_id: int, db: Session):
    """Delete shift type"""
    response = Response(
        status_code=200,
    )
    shift_type_repository.delete_shift_type_and_relations(
        db=db,
        shift_type_id=shift_type_id
    )
    
    shift_types = shift_type_repository.list_user_shift_types(db=db, user_id=current_user.id)

    if not shift_types:
        response.headers["HX-Redirect"] = "/shifts/setup/"
        
    return response
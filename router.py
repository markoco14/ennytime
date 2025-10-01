from fastapi import APIRouter, Depends

from app.auth import auth_service
from app.controllers import calendar, public, shifts 

# from controllers import classes, public
# from dependencies import requires_owner, requires_user

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/",                                                public.index,       [Depends(auth_service.user_dependency)]),

    ("GET",     "/calendar/{year}/{month}",                         calendar.month,     [Depends(auth_service.user_dependency)]),
    ("GET",     "/calendar/{year}/{month}/{day}",                   calendar.day,       [Depends(auth_service.user_dependency)]),

    ("GET",     "/shifts",                                          shifts.index,       [Depends(auth_service.user_dependency)]),
    ("GET",     "/shifts/new",                                      shifts.new,         [Depends(auth_service.user_dependency)]),
    ("POST",    "/shifts/new",                                      shifts.create,      [Depends(auth_service.user_dependency)]),
    ("GET",     "/shifts/{shift_type_id}/edit",                     shifts.edit,        [Depends(auth_service.user_dependency)]),
    ("POST",    "/shifts/{shift_type_id}/edit",                     shifts.update,      [Depends(auth_service.user_dependency)]),
    ("DELETE",  "/shifts/{shift_type_id}",                          shifts.delete,      [Depends(auth_service.user_dependency)]),
    ("GET",     "/shifts/setup",                                    shifts.setup,       [Depends(auth_service.user_dependency)]),
]

for method, path, handler, deps in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=deps or None
    )



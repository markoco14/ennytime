from fastapi import APIRouter, Depends

from app.auth import auth_service
from app.controllers import calendar, public, schedule, shifts , profile

# from controllers import classes, public
# from dependencies import requires_owner, requires_user

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/",                                                public.index,               [Depends(auth_service.user_dependency)]),   # None

    ("GET",     "/calendar/{year}/{month}",                         calendar.month,             [Depends(auth_service.user_dependency)]),   # User
    ("GET",     "/calendar/{year}/{month}/{day}",                   calendar.day,               [Depends(auth_service.user_dependency)]),   # User

    ("GET",     "/shifts",                                          shifts.index,               [Depends(auth_service.user_dependency)]),   # User
    ("GET",     "/shifts/new",                                      shifts.new,                 [Depends(auth_service.user_dependency)]),   # User
    ("POST",    "/shifts/new",                                      shifts.create,              [Depends(auth_service.user_dependency)]),   # User
    ("GET",     "/shifts/{shift_type_id}/edit",                     shifts.edit,                [Depends(auth_service.user_dependency)]),   # Owner?
    ("POST",    "/shifts/{shift_type_id}/edit",                     shifts.update,              [Depends(auth_service.user_dependency)]),   # Owner?
    ("DELETE",  "/shifts/{shift_type_id}",                          shifts.delete,              [Depends(auth_service.user_dependency)]),   # Owner?
    ("GET",     "/shifts/setup",                                    shifts.setup,               [Depends(auth_service.user_dependency)]),   # User

    ("GET",     "/scheduling",                                      schedule.index,             [Depends(auth_service.user_dependency)]),   # user
    ("GET",     "/scheduling/{year}/{month}",                       schedule.month,             [Depends(auth_service.user_dependency)]),   # user
    ("POST",    "/scheduling/{date}/{type_id}",                     schedule.create,            [Depends(auth_service.user_dependency)]),   # user
    ("DELETE",  "/scheduling/{date}/{type_id}",                     schedule.delete,            [Depends(auth_service.user_dependency)]),   # owner?

    ("GET",     "/profile",                                         profile.index,              [Depends(auth_service.user_dependency)]),   # user
    ("GET",     "/profile/display-name/{user_id}",                  profile.display_name,       [Depends(auth_service.user_dependency)]),   # owner?
    ("PUT",     "/profile/display-name/edit/{user_id}",             profile.update,             [Depends(auth_service.user_dependency)]),   # owner?
    ("GET",     "/profile/display-name/edit/{user_id}",             profile.edit,               [Depends(auth_service.user_dependency)]),   # owner?
    ("GET",     "/birthday/{user_id}",                              profile.birthday,           [Depends(auth_service.user_dependency)]),   # owner?
    ("PUT",     "/birthday/{user_id}",                              profile.update_birthday,    [Depends(auth_service.user_dependency)]),   # owner?
    ("GET",     "/birthday/{user_id}/edit",                         profile.birthday_edit,      [Depends(auth_service.user_dependency)]),   # owner?
    ("GET",     "/username/{user_id}",                              profile.username,           [Depends(auth_service.user_dependency)]),   # owner?
    ("PUT",     "/username/{user_id}",                              profile.update_username,    [Depends(auth_service.user_dependency)]),   # owner?
    ("POST",    "/username-unique",                                 profile.unique,             [Depends(auth_service.user_dependency)]),   # owner?
]

for method, path, handler, deps in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=deps or None
    )



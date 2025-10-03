from fastapi import APIRouter, Depends

from app.auth import auth_service
from app.controllers import admin, calendar, public, relationships, schedule, shifts , profile

# from controllers import classes, public
# from dependencies import requires_owner, requires_user

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/",                                    public.index,               [Depends(auth_service.requires_guest)]),   # None

    ("GET",     "/calendar/{year}/{month}",             calendar.month,             [Depends(auth_service.requires_user)]),   # User
    ("GET",     "/calendar/{year}/{month}/{day}",       calendar.day,               [Depends(auth_service.user_dependency)]),   # User

    ("GET",     "/calendar/{year}/{month}/{day}/edit",  calendar.get_calendar_day_edit, [Depends(auth_service.user_dependency)]),
    ("POST",    "/calendar/card/{date_string}/edit/{shift_type_id}", calendar.get_calendar_card_edit, [Depends(auth_service.user_dependency)]),
    ("DELETE",  "/calendar/card/{date_string}/edit/{shift_type_id}", calendar.delete_shift_for_date, [Depends(auth_service.user_dependency)]),


    ("GET",     "/shifts",                              shifts.index,               [Depends(auth_service.user_dependency)]),   # User
    ("GET",     "/shifts/new",                          shifts.new,                 [Depends(auth_service.user_dependency)]),   # User
    ("POST",    "/shifts/new",                          shifts.create,              [Depends(auth_service.user_dependency)]),   # User
    ("GET",     "/shifts/{shift_type_id}/edit",         shifts.edit,                [Depends(auth_service.user_dependency)]),   # Owner?
    ("POST",    "/shifts/{shift_type_id}/edit",         shifts.update,              [Depends(auth_service.user_dependency)]),   # Owner?
    ("DELETE",  "/shifts/{shift_type_id}",              shifts.delete,              [Depends(auth_service.user_dependency)]),   # Owner?
    ("GET",     "/shifts/setup",                        shifts.setup,               [Depends(auth_service.user_dependency)]),   # User

    ("GET",     "/scheduling",                          schedule.index,             [Depends(auth_service.user_dependency)]),   # user
    ("GET",     "/scheduling/{year}/{month}",           schedule.month,             [Depends(auth_service.user_dependency)]),   # user
    ("POST",    "/scheduling/{date}/{type_id}",         schedule.create,            [Depends(auth_service.user_dependency)]),   # user
    ("DELETE",  "/scheduling/{date}/{type_id}",         schedule.delete,            [Depends(auth_service.user_dependency)]),   # owner?

    ("GET",     "/profile",                             profile.index,              [Depends(auth_service.user_dependency)]),   # user
    ("GET",     "/profile/display-name/{user_id}",      profile.display_name,       [Depends(auth_service.user_dependency)]),   # owner?
    ("PUT",     "/profile/display-name/edit/{user_id}", profile.update,             [Depends(auth_service.user_dependency)]),   # owner?
    ("GET",     "/profile/display-name/edit/{user_id}", profile.edit,               [Depends(auth_service.user_dependency)]),   # owner?
    ("GET",     "/birthday/{user_id}",                  profile.birthday,           [Depends(auth_service.user_dependency)]),   # owner?
    ("PUT",     "/birthday/{user_id}",                  profile.update_birthday,    [Depends(auth_service.user_dependency)]),   # owner?
    ("GET",     "/birthday/{user_id}/edit",             profile.birthday_edit,      [Depends(auth_service.user_dependency)]),   # owner?
    ("GET",     "/username/{user_id}",                  profile.username,           [Depends(auth_service.user_dependency)]),   # owner?
    ("PUT",     "/username/{user_id}",                  profile.update_username,    [Depends(auth_service.user_dependency)]),   # owner?
    ("POST",    "/username-unique",                     profile.unique,             [Depends(auth_service.user_dependency)]),   # owner?

    ("GET",     "/share-calendar/{receiver_id}",        relationships.share,        [Depends(auth_service.user_dependency)]),   # user?
    ("DELETE",  "/share-calendar/{share_id}",           relationships.unshare,      [Depends(auth_service.user_dependency)]),   # in_relationship?
    ("DELETE",  "/reject-calendar/{share_id}",          relationships.reject,       [Depends(auth_service.user_dependency)]),   # in_relationship?
    ("POST",    "/search",                              relationships.search,       [Depends(auth_service.user_dependency)]),   # user?

    ("GET",     "/admin",                               admin.index,                [Depends(auth_service.user_dependency)]),
    ("GET",     "/admin/users",                         admin.list_users,           [Depends(auth_service.user_dependency)]),
    ("GET",     "/admin/user-signins",                  admin.list_user_signins,    [Depends(auth_service.user_dependency)]),
    ("DELETE",  "/admin/users/{user_id}",               admin.delete_user,          [Depends(auth_service.user_dependency)]),
]

for method, path, handler, deps in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=deps or None
    )



from fastapi import APIRouter, Depends

from app.auth import auth_service
from app.controllers import admin, auth, calendar, public, relationships, schedule, shifts , users
from app.dependencies import requires_admin, requires_profile_owner, requires_schedule_owner, requires_guest, requires_shift_owner, requires_user

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/",                                    public.index,               requires_guest),   # None

    ("GET",     "/signup",                              auth.get_signup_page,       requires_guest),
    ("POST",    "/signup",                              auth.signup,                requires_guest),
    ("GET",     "/signin",                              auth.get_signin_page,       requires_guest),
    ("POST",    "/signin",                              auth.signin,                requires_guest),
    ("GET",     "/signout",                             auth.signout,               requires_user),

    ("GET",     "/calendar/{year}/{month}",             calendar.month,             requires_user),   # User
    ("GET",     "/calendar/{year}/{month}/{day}",       calendar.day,               requires_user),   # User
    ("GET",     "/calendar/{year}/{month}/{day}/edit",  calendar.edit,              requires_user),

    ("GET",     "/shifts",                              shifts.index,               requires_user),
    ("GET",     "/shifts/new",                          shifts.new,                 requires_user),
    ("POST",    "/shifts/new",                          shifts.create,              requires_user),
    ("GET",     "/shifts/{shift_type_id}/edit",         shifts.edit,                requires_shift_owner),
    ("POST",    "/shifts/{shift_type_id}/edit",         shifts.update,              requires_shift_owner),
    ("DELETE",  "/shifts/{shift_type_id}",              shifts.delete,              requires_shift_owner),

    ("GET",     "/scheduling",                          schedule.index,             requires_user),   # user
    ("GET",     "/scheduling/{year}/{month}",           schedule.month,             requires_user),   # user
    ("POST",    "/scheduling",                          schedule.create,            requires_user),   # user
    ("DELETE",  "/scheduling/{schedule_id}",            schedule.delete,            requires_schedule_owner),   # owner?


    ("GET",     "/profile",                             users.profile,              requires_user),   # user
    ("PUT",     "/users/{user_id}",                     users.update,               requires_profile_owner),
    ("POST",    "/username-unique",                     users.unique,               requires_user),   # owner?

    # ("GET",     "/share-calendar/{receiver_id}",        relationships.share,        auth_service.user_dependency),   # user?
    # ("DELETE",  "/share-calendar/{share_id}",           relationships.unshare,      auth_service.user_dependency),   # in_relationship?
    # ("DELETE",  "/reject-calendar/{share_id}",          relationships.reject,       auth_service.user_dependency),   # in_relationship?
    # ("POST",    "/search",                              relationships.search,       auth_service.user_dependency),   # user?

    ("GET",     "/admin",                               admin.index,                requires_admin),
    ("GET",     "/admin/users",                         admin.users,                requires_admin),
    ("GET",     "/admin/signins",                       admin.signins,              requires_admin),
]

for method, path, handler, _ in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
    )



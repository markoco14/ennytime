from fastapi import APIRouter, Depends

from app.auth import auth_service
from app.controllers import public

# from controllers import classes, public
# from dependencies import requires_owner, requires_user

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/",                                                public.index,    [Depends(auth_service.user_dependency)]),
]

for method, path, handler, deps in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=deps or None
    )



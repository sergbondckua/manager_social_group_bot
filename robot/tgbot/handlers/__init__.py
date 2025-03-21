from .admin import admin_router
from .echo import echo_router
from .member import member_router
from .user import user_router

routers_list = [
    admin_router,
    member_router,
    user_router,
    echo_router,  # echo_router must be last
]

__all__ = ["routers_list"]

from .admin import admin_router
from .echo import echo_router
from .member.profile import profile_router
from .member.start import member_router
from .staff.create_training import staff_router
from .user import user_router

routers_list = [
    staff_router,
    member_router,
    profile_router,
    user_router,
    admin_router,
    # echo_router,  # echo_router must be last
]

__all__ = ["routers_list"]

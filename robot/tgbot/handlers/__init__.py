from .admin import admin_router
from .echo import echo_router
from .member.member import rating_comment_router
from .member.profile import profile_router
from .member.start import member_router
from .staff.training_event import staff_router
from .user.register_training import reg_training_router
from .user.users import user_router

routers_list = [
    staff_router,
    member_router,
    rating_comment_router,
    profile_router,
    user_router,
    reg_training_router,
    admin_router,
    # echo_router,  # echo_router must be last
]

__all__ = ["routers_list"]

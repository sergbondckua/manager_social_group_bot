from .deeplink import deep_link_router
from .echo import echo_router
from .quiz import quiz_router

routers_list = [
    quiz_router,
    deep_link_router,
    echo_router,  # echo_router must be last
]

__all__ = ["routers_list"]

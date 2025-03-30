from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/bank/", include("bank.urls_admin")),
    path("admin/", admin.site.urls),
    path("bank/", include("bank.urls")),
    path("robot/", include("robot.urls")),
]

if settings.DEBUG:
    # Serve media files
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

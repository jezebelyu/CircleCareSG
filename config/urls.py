from django.contrib import admin
from django.urls import include, path

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "",
        include("mainWebsite.urls"),
    ),

    path(
        "accounts/",
        include("accounts.urls"),
    ),

    path(
        "senior/",
        include("seniorPortal.urls"),
    ),

    path(
        "volunteer/",
        include("volunteerPortal.urls"),
    ),

    path(
        "admin-portal/",
        include("adminPortal.urls"),
    ),
    
    path(
        "guardian/",
        include("guardianPortal.urls"),
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
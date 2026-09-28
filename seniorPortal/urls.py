from django.urls import path

from . import views


urlpatterns = [
    path(
        "dashboard/",
        views.senior_dashboard,
        name="senior_dashboard",
    ),
    path(
        "wellbeing/",
        views.senior_wellbeing,
        name="senior_wellbeing",
    ),
    path(
        "check-in-history/",
        views.check_in_history,
        name="check_in_history",
    ),
    path(
        "profile/",
        views.senior_profile,
        name="senior_profile",
    ),
    path(
        "profile/edit/",
        views.edit_senior_profile,
        name="edit_senior_profile",
    ),
    path(
        "support-requests/",
        views.support_request_history,
        name="support_request_history",
    ),
    path(
        "support-requests/new/",
        views.support_request_select,
        name="support_request_select",
    ),
    path(
        "support-requests/new/details/",
        views.support_request_details,
        name="support_request_details",
    ),
    path(
        "my-volunteer/",
        views.senior_volunteer,
        name="senior_volunteer",
    ),
]
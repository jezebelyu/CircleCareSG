from django.urls import path

from . import views


urlpatterns = [
    # Dashboard
    path(
        "dashboard/",
        views.guardian_dashboard,
        name="guardian_dashboard",
    ),

    # My senior
    path(
        "my-senior/",
        views.guardian_my_senior,
        name="guardian_my_senior",
    ),
    path(
        "my-senior/edit/",
        views.guardian_edit_senior,
        name="guardian_edit_senior",
    ),

    # Contact volunteer
    path(
        "contact-volunteer/",
        views.guardian_contact_volunteer,
        name="guardian_contact_volunteer",
    ),

    # Check-in reports
    path(
        "check-in-reports/",
        views.guardian_check_in_reports,
        name="guardian_check_in_reports",
    ),
    path(
        "check-in-reports/volunteer/<int:report_id>/",
        views.guardian_view_volunteer_report,
        name="guardian_view_volunteer_report",
    ),
    path(
        "check-in-reports/phone/<int:visit_id>/",
        views.guardian_view_phone_check_in,
        name="guardian_view_phone_check_in",
    ),
    path(
        "check-in-reports/wellbeing/<int:wellbeing_id>/",
        views.guardian_view_wellbeing_submission,
        name="guardian_view_wellbeing_submission",
    ),

    # Alerts
    path(
        "alerts/",
        views.guardian_alerts,
        name="guardian_alerts",
    ),

    # Profile
    path(
        "profile/",
        views.guardian_profile,
        name="guardian_profile",
    ),
    path(
        "profile/edit/",
        views.guardian_edit_profile,
        name="guardian_edit_profile",
    ),
]
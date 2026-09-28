from django.urls import path

from . import views


urlpatterns = [
    # Dashboard
    path(
        "dashboard/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),

    # Seniors
    path(
        "seniors/",
        views.admin_seniors,
        name="admin_seniors",
    ),
    path(
        "seniors/add/",
        views.admin_add_senior,
        name="admin_add_senior",
    ),
    path(
        "seniors/<int:senior_id>/",
        views.admin_senior_detail,
        name="admin_senior_detail",
    ),
    path(
        "seniors/<int:senior_id>/edit/",
        views.admin_edit_senior,
        name="admin_edit_senior",
    ),

    # Volunteers
    path(
        "volunteers/",
        views.admin_volunteers,
        name="admin_volunteers",
    ),
    path(
        "volunteers/add/",
        views.admin_add_volunteer,
        name="admin_add_volunteer",
    ),
    path(
        "volunteers/<int:volunteer_id>/",
        views.admin_volunteer_detail,
        name="admin_volunteer_detail",
    ),
    path(
        "volunteers/<int:volunteer_id>/edit/",
        views.admin_edit_volunteer,
        name="admin_edit_volunteer",
    ),
    path(
        "volunteers/<int:volunteer_id>/assign-senior/",
        views.admin_assign_senior_to_volunteer,
        name="admin_assign_senior_to_volunteer",
    ),
    path(
        "volunteer-assignments/<int:assignment_id>/remove/",
        views.admin_remove_senior_from_volunteer,
        name="admin_remove_senior_from_volunteer",
    ),

    # Visits and scheduling
    path(
        "visits-schedule/",
        views.admin_visits_schedule,
        name="admin_visits_schedule",
    ),
    path(
        "schedule-visit/",
        views.admin_schedule_visit,
        name="admin_schedule_visit",
    ),
    path(
        "visit/<int:visit_id>/",
        views.admin_visit_detail,
        name="admin_visit_detail",
    ),
    path(
        "visit/<int:visit_id>/edit/",
        views.admin_edit_visit,
        name="admin_edit_visit",
    ),

    # Reports
    path(
        "reports/",
        views.admin_reports,
        name="admin_reports",
    ),
    path(
        "reports/<int:report_id>/",
        views.admin_view_report,
        name="admin_view_report",
    ),

    # Support requests
    path(
        "support-requests/",
        views.admin_support_requests,
        name="admin_support_requests",
    ),
    path(
        "support-requests/<int:request_id>/",
        views.admin_support_request_detail,
        name="admin_support_request_detail",
    ),

    # Alerts
    path(
        "alerts/",
        views.admin_alerts,
        name="admin_alerts",
    ),
    path(
        "alerts/<int:submission_id>/",
        views.admin_alert_detail,
        name="admin_alert_detail",
    ),

    # Admin profile
    path(
        "profile/",
        views.admin_profile,
        name="admin_profile",
    ),
    path(
        "profile/edit/",
        views.admin_edit_profile,
        name="admin_edit_profile",
    ),
]
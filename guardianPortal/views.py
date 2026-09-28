from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from accounts.models import (
    AppUser,
    EmergencyContact,
    GuardianProfile,
    SeniorVolunteerAssignment,
)
from adminPortal.models import ScheduledVisit
from seniorPortal.models import WellbeingSubmission
from volunteerPortal.models import VisitReport

from .forms import GuardianProfileForm, GuardianSeniorForm


# ==================================================
# GUARDIAN ACCESS HELPER
# ==================================================

def get_guardian_context(request):
    """
    Return the logged-in AppUser, GuardianProfile,
    linked SeniorProfile, and an error redirect.

    The helper keeps Guardian authentication and profile
    checks consistent across all Guardian Portal views.
    """

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )

        return None, None, None, redirect("home")

    if app_user.account_type != "guardian":
        messages.error(
            request,
            "You do not have permission to access the Guardian Portal.",
        )

        return None, None, None, redirect("home")

    try:
        guardian_profile = (
            GuardianProfile.objects
            .select_related(
                "app_user",
                "app_user__user",
                "linked_senior",
                "linked_senior__app_user",
                "linked_senior__app_user__user",
            )
            .get(app_user=app_user)
        )

    except GuardianProfile.DoesNotExist:
        messages.error(
            request,
            "Your Guardian profile could not be found.",
        )

        return None, None, None, redirect("home")

    linked_senior = guardian_profile.linked_senior

    return (
        app_user,
        guardian_profile,
        linked_senior,
        None,
    )


# ==================================================
# GUARDIAN DASHBOARD
# ==================================================

@login_required(login_url="login")
def guardian_dashboard(request):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    # ==================================================
    # DEFAULT VALUES
    # ==================================================

    active_assignment = None
    assigned_volunteer = None

    latest_wellbeing = None
    upcoming_visit = None
    latest_report = None

    latest_alert = None
    active_alert_count = 0

    # ==================================================
    # LINKED SENIOR DATA
    # ==================================================

    if linked_senior:

        # ----------------------------------------------
        # ACTIVE VOLUNTEER ASSIGNMENT
        # ----------------------------------------------

        active_assignment = (
            SeniorVolunteerAssignment.objects
            .filter(
                senior=linked_senior,
                active=True,
            )
            .select_related(
                "volunteer",
                "volunteer__app_user",
            )
            .order_by("-assigned_at")
            .first()
        )

        if active_assignment:
            assigned_volunteer = active_assignment.volunteer

        # ----------------------------------------------
        # LATEST WELLBEING SUBMISSION
        # ----------------------------------------------

        latest_wellbeing = (
            WellbeingSubmission.objects
            .filter(senior=linked_senior)
            .order_by("-submitted_at")
            .first()
        )

        # ----------------------------------------------
        # UPCOMING VISIT
        # ----------------------------------------------

        upcoming_visit = (
            ScheduledVisit.objects
            .filter(
                assignment__senior=linked_senior,
                status="scheduled",
                visit_date__gte=date.today(),
            )
            .select_related(
                "assignment",
                "assignment__volunteer",
                "assignment__volunteer__app_user",
            )
            .order_by(
                "visit_date",
                "start_time",
            )
            .first()
        )

        # ----------------------------------------------
        # LATEST VOLUNTEER REPORT
        # ----------------------------------------------

        latest_report = (
            VisitReport.objects
            .filter(
                visit__assignment__senior=linked_senior
            )
            .select_related(
                "visit",
                "visit__assignment",
                "visit__assignment__volunteer",
                "visit__assignment__volunteer__app_user",
            )
            .order_by("-submitted_at")
            .first()
        )

        # ----------------------------------------------
        # DASHBOARD ALERTS
        # ----------------------------------------------

        dashboard_alerts = []

        wellbeing_alerts = (
            WellbeingSubmission.objects
            .filter(
                senior=linked_senior,
                feeling__in=[
                    "not_good",
                    "need_support",
                ],
            )
            .order_by("-submitted_at")
        )

        for submission in wellbeing_alerts:
            dashboard_alerts.append(
                {
                    "type": "Wellbeing Alert",
                    "feeling": submission.get_feeling_display(),
                    "comment": submission.notes or "",
                    "date": submission.submitted_at,
                    "priority": "high",
                }
            )

        volunteer_alerts = (
            VisitReport.objects
            .filter(
                visit__assignment__senior=linked_senior
            )
            .order_by("-submitted_at")
        )

        for report in volunteer_alerts:

            if (
                report.wellbeing_status == "concern"
                or report.follow_up_required
                or report.concerns.strip()
            ):
                dashboard_alerts.append(
                    {
                        "type": "Volunteer Alert",
                        "feeling": (
                            report.get_wellbeing_status_display()
                        ),
                        "comment": (
                            report.concerns
                            or report.follow_up_notes
                            or "Follow-up required."
                        ),
                        "date": report.submitted_at,
                        "priority": "medium",
                    }
                )

        dashboard_alerts.sort(
            key=lambda alert: alert["date"],
            reverse=True,
        )

        active_alert_count = len(dashboard_alerts)

        if dashboard_alerts:
            latest_alert = dashboard_alerts[0]

    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "guardianPortal/dashboard.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "active_assignment": active_assignment,
            "assigned_volunteer": assigned_volunteer,
            "latest_wellbeing": latest_wellbeing,
            "upcoming_visit": upcoming_visit,
            "latest_report": latest_report,
            "latest_alert": latest_alert,
            "active_alert_count": active_alert_count,
        },
    )


# ==================================================
# GUARDIAN - MY SENIOR
# ==================================================

@login_required(login_url="login")
def guardian_my_senior(request):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    emergency_contact = None

    upcoming_visits = ScheduledVisit.objects.none()
    previous_reports = VisitReport.objects.none()

    # ==================================================
    # LINKED SENIOR DATA
    # ==================================================

    if linked_senior:

        # ----------------------------------------------
        # EMERGENCY CONTACT
        # ----------------------------------------------

        try:
            emergency_contact = linked_senior.emergency_contact

        except EmergencyContact.DoesNotExist:
            emergency_contact = None

        # ----------------------------------------------
        # UPCOMING VISITS
        # ----------------------------------------------

        upcoming_visits = (
            ScheduledVisit.objects
            .filter(
                assignment__senior=linked_senior,
                status="scheduled",
                visit_date__gte=date.today(),
            )
            .select_related(
                "assignment",
                "assignment__volunteer",
                "assignment__volunteer__app_user",
            )
            .order_by(
                "visit_date",
                "start_time",
            )[:3]
        )

        # ----------------------------------------------
        # PREVIOUS REPORTS
        # ----------------------------------------------

        previous_reports = (
            VisitReport.objects
            .filter(
                visit__assignment__senior=linked_senior
            )
            .select_related(
                "visit",
                "visit__assignment",
                "visit__assignment__volunteer",
                "visit__assignment__volunteer__app_user",
            )
            .order_by("-submitted_at")[:3]
        )

    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "guardianPortal/my_senior.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "emergency_contact": emergency_contact,
            "upcoming_visits": upcoming_visits,
            "previous_reports": previous_reports,
        },
    )


# ==================================================
# GUARDIAN - EDIT LINKED SENIOR
# ==================================================

@login_required(login_url="login")
def guardian_edit_senior(request):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    # ==================================================
    # REQUIRE LINKED SENIOR
    # ==================================================

    if not linked_senior:
        messages.error(
            request,
            "A senior has not been linked to your Guardian account.",
        )

        return redirect("guardian_my_senior")

    senior_app_user = linked_senior.app_user

    # ==================================================
    # EMERGENCY CONTACT
    # ==================================================

    try:
        emergency_contact = linked_senior.emergency_contact

    except EmergencyContact.DoesNotExist:
        emergency_contact = None

    # ==================================================
    # PROCESS FORM
    # ==================================================

    if request.method == "POST":

        form = GuardianSeniorForm(request.POST)

        if form.is_valid():

            with transaction.atomic():

                # --------------------------------------
                # APP USER
                # --------------------------------------

                senior_app_user.full_name = (
                    form.cleaned_data["full_name"]
                )

                senior_app_user.mobile_number = (
                    form.cleaned_data["mobile_number"]
                )

                senior_app_user.date_of_birth = (
                    form.cleaned_data["date_of_birth"]
                )

                senior_app_user.save(
                    update_fields=[
                        "full_name",
                        "mobile_number",
                        "date_of_birth",
                    ]
                )

                # --------------------------------------
                # SENIOR PROFILE
                # --------------------------------------

                linked_senior.address = (
                    form.cleaned_data["address"]
                )

                linked_senior.unit_number = (
                    form.cleaned_data["unit_number"]
                )

                linked_senior.postal_code = (
                    form.cleaned_data["postal_code"]
                )

                linked_senior.preferred_language = (
                    form.cleaned_data["preferred_language"]
                )

                linked_senior.allergies = (
                    form.cleaned_data["allergies"]
                )

                linked_senior.medical_conditions = (
                    form.cleaned_data[
                        "medical_conditions"
                    ]
                )

                linked_senior.religion = (
                    form.cleaned_data["religion"]
                )

                linked_senior.regular_check_ins = (
                    form.cleaned_data[
                        "regular_check_ins"
                    ]
                )

                linked_senior.mobility_assistance = (
                    form.cleaned_data[
                        "mobility_assistance"
                    ]
                )

                linked_senior.meal_assistance = (
                    form.cleaned_data[
                        "meal_assistance"
                    ]
                )

                linked_senior.emotional_support = (
                    form.cleaned_data[
                        "emotional_support"
                    ]
                )

                linked_senior.medical_assistance = (
                    form.cleaned_data[
                        "medical_assistance"
                    ]
                )

                linked_senior.other_support = (
                    form.cleaned_data["other_support"]
                )

                linked_senior.save()

                # --------------------------------------
                # EMERGENCY CONTACT
                # --------------------------------------

                contact_name = (
                    form.cleaned_data[
                        "emergency_contact_name"
                    ]
                )

                contact_relationship = (
                    form.cleaned_data[
                        "emergency_contact_relationship"
                    ]
                )

                contact_mobile = (
                    form.cleaned_data[
                        "emergency_contact_mobile"
                    ]
                )

                if (
                    contact_name
                    or contact_relationship
                    or contact_mobile
                ):
                    EmergencyContact.objects.update_or_create(
                        senior=linked_senior,
                        defaults={
                            "full_name": contact_name,
                            "relationship": contact_relationship,
                            "mobile_number": contact_mobile,
                        },
                    )

            messages.success(
                request,
                "Senior profile updated successfully.",
            )

            return redirect("guardian_my_senior")

    else:

        form = GuardianSeniorForm(
            initial={
                "full_name": (
                    senior_app_user.full_name
                ),
                "mobile_number": (
                    senior_app_user.mobile_number
                ),
                "date_of_birth": (
                    senior_app_user.date_of_birth
                ),
                "address": linked_senior.address,
                "unit_number": linked_senior.unit_number,
                "postal_code": linked_senior.postal_code,
                "preferred_language": (
                    linked_senior.preferred_language
                ),
                "allergies": linked_senior.allergies,
                "medical_conditions": (
                    linked_senior.medical_conditions
                ),
                "religion": linked_senior.religion,
                "regular_check_ins": (
                    linked_senior.regular_check_ins
                ),
                "mobility_assistance": (
                    linked_senior.mobility_assistance
                ),
                "meal_assistance": (
                    linked_senior.meal_assistance
                ),
                "emotional_support": (
                    linked_senior.emotional_support
                ),
                "medical_assistance": (
                    linked_senior.medical_assistance
                ),
                "other_support": (
                    linked_senior.other_support
                ),
                "emergency_contact_name": (
                    emergency_contact.full_name
                    if emergency_contact
                    else ""
                ),
                "emergency_contact_relationship": (
                    emergency_contact.relationship
                    if emergency_contact
                    else ""
                ),
                "emergency_contact_mobile": (
                    emergency_contact.mobile_number
                    if emergency_contact
                    else ""
                ),
            }
        )

    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "guardianPortal/edit_senior.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "form": form,
        },
    )


# ==================================================
# GUARDIAN - CONTACT VOLUNTEER
# ==================================================

@login_required(login_url="login")
def guardian_contact_volunteer(request):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    active_assignment = None
    assigned_volunteer = None

    if linked_senior:

        active_assignment = (
            SeniorVolunteerAssignment.objects
            .filter(
                senior=linked_senior,
                active=True,
            )
            .select_related(
                "volunteer",
                "volunteer__app_user",
                "volunteer__app_user__user",
            )
            .order_by("-assigned_at")
            .first()
        )

        if active_assignment:
            assigned_volunteer = active_assignment.volunteer

    return render(
        request,
        "guardianPortal/contact_volunteer.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "active_assignment": active_assignment,
            "assigned_volunteer": assigned_volunteer,
        },
    )


# ==================================================
# GUARDIAN - CHECK-IN REPORTS
# ==================================================

@login_required(login_url="login")
def guardian_check_in_reports(request):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    volunteer_reports = VisitReport.objects.none()
    wellbeing_submissions = WellbeingSubmission.objects.none()
    phone_check_ins = ScheduledVisit.objects.none()

    # ==================================================
    # LINKED SENIOR REPORT DATA
    # ==================================================

    if linked_senior:

        volunteer_reports = (
            VisitReport.objects
            .filter(
                visit__assignment__senior=linked_senior
            )
            .select_related(
                "visit",
                "visit__assignment",
                "visit__assignment__volunteer",
                "visit__assignment__volunteer__app_user",
            )
            .order_by("-submitted_at")
        )

        wellbeing_submissions = (
            WellbeingSubmission.objects
            .filter(senior=linked_senior)
            .order_by("-submitted_at")
        )

        phone_check_ins = (
            ScheduledVisit.objects
            .filter(
                assignment__senior=linked_senior,
                visit_type="phone_call",
                status="completed",
            )
            .select_related(
                "assignment",
                "assignment__volunteer",
                "assignment__volunteer__app_user",
            )
            .order_by(
                "-visit_date",
                "-start_time",
            )
        )

    completed_check_ins_count = (
        volunteer_reports.count()
        + phone_check_ins.count()
    )

    return render(
        request,
        "guardianPortal/check_in_reports.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "volunteer_reports": volunteer_reports,
            "wellbeing_submissions": wellbeing_submissions,
            "phone_check_ins": phone_check_ins,
            "completed_check_ins_count": (
                completed_check_ins_count
            ),
        },
    )


# ==================================================
# GUARDIAN - VIEW VOLUNTEER REPORT
# ==================================================

@login_required(login_url="login")
def guardian_view_volunteer_report(
    request,
    report_id,
):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    if not linked_senior:
        messages.error(
            request,
            "A senior has not been linked to your Guardian account.",
        )

        return redirect(
            "guardian_check_in_reports"
        )

    # ==================================================
    # GET REPORT
    # ==================================================

    try:
        report = (
            VisitReport.objects
            .select_related(
                "visit",
                "visit__assignment",
                "visit__assignment__senior",
                "visit__assignment__senior__app_user",
                "visit__assignment__volunteer",
                "visit__assignment__volunteer__app_user",
            )
            .get(
                id=report_id,
                visit__assignment__senior=linked_senior,
            )
        )

    except VisitReport.DoesNotExist:
        messages.error(
            request,
            "The requested report could not be found.",
        )

        return redirect(
            "guardian_check_in_reports"
        )

    return render(
        request,
        "guardianPortal/view_volunteer_report.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "report": report,
            "visit": report.visit,
        },
    )


# ==================================================
# GUARDIAN - VIEW PHONE CHECK-IN
# ==================================================

@login_required(login_url="login")
def guardian_view_phone_check_in(
    request,
    visit_id,
):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    if not linked_senior:
        messages.error(
            request,
            "A senior has not been linked to your Guardian account.",
        )

        return redirect(
            "guardian_check_in_reports"
        )

    # ==================================================
    # GET PHONE CHECK-IN
    # ==================================================

    try:
        visit = (
            ScheduledVisit.objects
            .select_related(
                "assignment",
                "assignment__senior",
                "assignment__senior__app_user",
                "assignment__volunteer",
                "assignment__volunteer__app_user",
            )
            .get(
                id=visit_id,
                assignment__senior=linked_senior,
                visit_type="phone_call",
                status="completed",
            )
        )

    except ScheduledVisit.DoesNotExist:
        messages.error(
            request,
            "The requested phone check-in could not be found.",
        )

        return redirect(
            "guardian_check_in_reports"
        )

    # ==================================================
    # OPTIONAL VISIT REPORT
    # ==================================================

    try:
        report = visit.visit_report

    except VisitReport.DoesNotExist:
        report = None

    return render(
        request,
        "guardianPortal/view_phone_check_in.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "visit": visit,
            "report": report,
        },
    )


# ==================================================
# GUARDIAN - VIEW WELLBEING SUBMISSION
# ==================================================

@login_required(login_url="login")
def guardian_view_wellbeing_submission(
    request,
    wellbeing_id,
):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    if not linked_senior:
        messages.error(
            request,
            "A senior has not been linked to your Guardian account.",
        )

        return redirect(
            "guardian_check_in_reports"
        )

    # ==================================================
    # GET WELLBEING SUBMISSION
    # ==================================================

    try:
        wellbeing = (
            WellbeingSubmission.objects
            .select_related(
                "senior",
                "senior__app_user",
            )
            .get(
                id=wellbeing_id,
                senior=linked_senior,
            )
        )

    except WellbeingSubmission.DoesNotExist:
        messages.error(
            request,
            "The requested wellbeing submission could not be found.",
        )

        return redirect(
            "guardian_check_in_reports"
        )

    return render(
        request,
        "guardianPortal/view_wellbeing_submission.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "wellbeing": wellbeing,
        },
    )


# ==================================================
# GUARDIAN - ALERTS
# ==================================================

@login_required(login_url="login")
def guardian_alerts(request):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    alerts = []

    # ==================================================
    # BUILD ALERT LIST
    # ==================================================

    if linked_senior:

        # ----------------------------------------------
        # WELLBEING ALERTS
        # ----------------------------------------------

        wellbeing_submissions = (
            WellbeingSubmission.objects
            .filter(senior=linked_senior)
            .order_by("-submitted_at")
        )

        for submission in wellbeing_submissions:

            if submission.feeling in [
                "not_good",
                "need_support",
            ]:
                priority = "high"
                status = "new"
                action_text = "Action Required"

            else:
                priority = "resolved"
                status = "resolved"
                action_text = "No Action Needed"

            alerts.append(
                {
                    "type": "Wellbeing Submission",
                    "priority": priority,
                    "status": status,
                    "action_text": action_text,
                    "summary": (
                        f"{linked_senior.app_user.full_name} "
                        f"reported feeling "
                        f"{submission.get_feeling_display()}."
                    ),
                    "date": submission.submitted_at,
                    "source": "wellbeing",
                    "source_id": submission.id,
                }
            )

        # ----------------------------------------------
        # VOLUNTEER REPORT ALERTS
        # ----------------------------------------------

        visit_reports = (
            VisitReport.objects
            .filter(
                visit__assignment__senior=linked_senior
            )
            .select_related(
                "visit",
                "visit__assignment",
                "visit__assignment__volunteer",
                "visit__assignment__volunteer__app_user",
            )
            .order_by("-submitted_at")
        )

        for report in visit_reports:

            if (
                report.wellbeing_status == "concern"
                or report.follow_up_required
                or report.concerns.strip()
            ):
                alerts.append(
                    {
                        "type": "Volunteer Report",
                        "priority": "medium",
                        "status": "pending",
                        "action_text": "Follow Up",
                        "summary": (
                            report.concerns
                            or report.follow_up_notes
                            or (
                                "Volunteer reported "
                                "a care concern."
                            )
                        ),
                        "date": report.submitted_at,
                        "source": "report",
                        "source_id": report.id,
                    }
                )

        # ----------------------------------------------
        # CANCELLED / MISSED VISITS
        # ----------------------------------------------

        cancelled_visits = (
            ScheduledVisit.objects
            .filter(
                assignment__senior=linked_senior,
                status="cancelled",
            )
            .select_related(
                "assignment",
                "assignment__volunteer",
                "assignment__volunteer__app_user",
            )
            .order_by(
                "-visit_date",
                "-start_time",
            )
        )

        for visit in cancelled_visits:

            visit_datetime = datetime.combine(
                visit.visit_date,
                visit.start_time,
            )

            alerts.append(
                {
                    "type": "Cancelled / Missed Visit",
                    "priority": "medium",
                    "status": "pending",
                    "action_text": "Follow Up",
                    "summary": (
                        f"{visit.get_visit_type_display()} "
                        "was cancelled or missed."
                    ),
                    "date": visit_datetime,
                    "source": "visit",
                    "source_id": visit.id,
                }
            )

    # ==================================================
    # SORT + COUNTS
    # ==================================================

    alerts.sort(
        key=lambda alert: alert["date"],
        reverse=True,
    )

    high_priority_count = sum(
        1
        for alert in alerts
        if alert["priority"] == "high"
    )

    medium_priority_count = sum(
        1
        for alert in alerts
        if alert["priority"] == "medium"
    )

    resolved_count = sum(
        1
        for alert in alerts
        if alert["priority"] == "resolved"
    )

    return render(
        request,
        "guardianPortal/alerts.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "alerts": alerts,
            "high_priority_count": high_priority_count,
            "medium_priority_count": medium_priority_count,
            "resolved_count": resolved_count,
        },
    )


# ==================================================
# GUARDIAN - MY PROFILE
# ==================================================

@login_required(login_url="login")
def guardian_profile(request):

    (
        app_user,
        guardian_profile_object,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    return render(
        request,
        "guardianPortal/profile.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile_object,
            "linked_senior": linked_senior,
        },
    )


# ==================================================
# GUARDIAN - EDIT MY PROFILE
# ==================================================

@login_required(login_url="login")
def guardian_edit_profile(request):

    (
        app_user,
        guardian_profile,
        linked_senior,
        error_response,
    ) = get_guardian_context(request)

    if error_response:
        return error_response

    # ==================================================
    # PROCESS FORM
    # ==================================================

    if request.method == "POST":

        form = GuardianProfileForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            with transaction.atomic():

                # --------------------------------------
                # APP USER
                # --------------------------------------

                app_user.full_name = (
                    form.cleaned_data["full_name"]
                )

                app_user.mobile_number = (
                    form.cleaned_data["mobile_number"]
                )

                update_fields = [
                    "full_name",
                    "mobile_number",
                ]

                # Update the picture only when a new one is uploaded.
                if form.cleaned_data.get("profile_picture"):

                    app_user.profile_picture = (
                        form.cleaned_data["profile_picture"]
                    )

                    update_fields.append(
                        "profile_picture"
                    )

                app_user.save(
                    update_fields=update_fields
                )

                # --------------------------------------
                # DJANGO USER
                # --------------------------------------

                request.user.email = (
                    form.cleaned_data["email"]
                )

                request.user.save(
                    update_fields=["email"]
                )

                # --------------------------------------
                # GUARDIAN PROFILE
                # --------------------------------------

                guardian_profile.preferred_contact_method = (
                    form.cleaned_data[
                        "preferred_contact_method"
                    ]
                )

                guardian_profile.preferred_language = (
                    form.cleaned_data[
                        "preferred_language"
                    ]
                )

                guardian_profile.relationship_to_senior = (
                    form.cleaned_data[
                        "relationship_to_senior"
                    ]
                )

                guardian_profile.save(
                    update_fields=[
                        "preferred_contact_method",
                        "preferred_language",
                        "relationship_to_senior",
                    ]
                )

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )

            return redirect("guardian_profile")

    else:

        form = GuardianProfileForm(
            initial={
                "full_name": app_user.full_name,
                "email": request.user.email,
                "mobile_number": app_user.mobile_number,
                "preferred_contact_method": (
                    guardian_profile.preferred_contact_method
                ),
                "preferred_language": (
                    guardian_profile.preferred_language
                ),
                "relationship_to_senior": (
                    guardian_profile.relationship_to_senior
                ),
            }
        )

    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "guardianPortal/edit_profile.html",
        {
            "app_user": app_user,
            "guardian_profile": guardian_profile,
            "linked_senior": linked_senior,
            "form": form,
        },
    )
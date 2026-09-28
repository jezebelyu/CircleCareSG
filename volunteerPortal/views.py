import json
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import (
    AppUser,
    SeniorVolunteerAssignment,
    VolunteerDocument,
    VolunteerProfile,
    EmergencyContact,
)
from adminPortal.models import ScheduledVisit
from seniorPortal.models import SupportRequest, WellbeingSubmission
from volunteerPortal.models import VisitReport, VolunteerAvailability

from .forms import (
    VisitReportForm,
    VolunteerAccountEditForm,
    VolunteerDocumentUploadForm,
    VolunteerProfileEditForm,
)


# ==================================================
# SHARED VOLUNTEER ACCESS HELPER
# ==================================================

def get_volunteer_context(request):
    """
    Return the logged-in AppUser and VolunteerProfile.

    If the account is invalid or does not belong to a volunteer,
    return a redirect response instead.
    """

    try:
        app_user = request.user.app_profile
    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return None, None, redirect("home")

    if app_user.account_type != "volunteer":
        messages.error(
            request,
            "You do not have permission to access the Volunteer Portal.",
        )
        return None, None, redirect("home")

    try:
        volunteer_profile = app_user.volunteer_profile
    except VolunteerProfile.DoesNotExist:
        messages.error(
            request,
            "Your volunteer profile could not be found.",
        )
        return None, None, redirect("home")

    return app_user, volunteer_profile, None


# ==================================================
# VOLUNTEER DASHBOARD
# ==================================================

@login_required(login_url="login")
def volunteer_dashboard(request):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    today = date.today()

    # ==================================================
    # ACTIVE ASSIGNMENTS
    # ==================================================

    active_assignments = (
        SeniorVolunteerAssignment.objects
        .filter(
            volunteer=volunteer_profile,
            active=True,
        )
        .select_related(
            "senior",
            "senior__app_user",
        )
    )

    assigned_senior_ids = active_assignments.values_list(
        "senior_id",
        flat=True,
    )

    # ==================================================
    # DASHBOARD STATISTICS
    # ==================================================

    upcoming_visits_count = (
        ScheduledVisit.objects
        .filter(
            assignment__volunteer=volunteer_profile,
            status="scheduled",
            visit_date__gte=today,
        )
        .count()
    )

    seniors_assigned_count = active_assignments.count()

    reports_submitted_count = (
        VisitReport.objects
        .filter(
            visit__assignment__volunteer=volunteer_profile,
        )
        .count()
    )

    completed_visits = (
        ScheduledVisit.objects
        .filter(
            assignment__volunteer=volunteer_profile,
            status="completed",
        )
        .only("estimated_duration")
    )

    total_completed_minutes = sum(
        visit.estimated_duration or 0
        for visit in completed_visits
    )

    volunteer_hours = round(
        total_completed_minutes / 60,
        1,
    )

    # ==================================================
    # TODAY'S SCHEDULE
    # ==================================================

    todays_schedule = (
        ScheduledVisit.objects
        .filter(
            assignment__volunteer=volunteer_profile,
            visit_date=today,
            status="scheduled",
        )
        .select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
        )
        .order_by("start_time")
    )

    # ==================================================
    # RECENT ACTIVITY
    # ==================================================
    #
    # Shows activity only for seniors currently assigned
    # to the logged-in volunteer.
    # ==================================================

    recent_activity = []

    # --------------------------------------------------
    # WELLBEING SUBMISSIONS
    # --------------------------------------------------

    wellbeing_submissions = (
        WellbeingSubmission.objects
        .filter(
            senior_id__in=assigned_senior_ids,
        )
        .select_related(
            "senior",
            "senior__app_user",
        )
        .order_by("-submitted_at")[:10]
    )

    for submission in wellbeing_submissions:
        senior_name = submission.senior.app_user.full_name

        if submission.feeling == "need_support":
            activity_type = "urgent"
            title = "Wellbeing Support Needed"
            description = (
                f"{senior_name} reported that they need support."
            )

        elif submission.feeling == "not_good":
            activity_type = "attention"
            title = "Wellbeing Concern"
            description = (
                f"{senior_name} reported that they are not feeling well."
            )

        else:
            activity_type = "wellbeing"
            title = "Wellbeing Check-In"
            description = (
                f"{senior_name} reported feeling "
                f"{submission.get_feeling_display()}."
            )

        recent_activity.append(
            {
                "type": activity_type,
                "title": title,
                "description": description,
                "senior": submission.senior,
                "timestamp": submission.submitted_at,
                "submission": submission,
            }
        )

        # Add a separate activity when Admin has resolved
        # a wellbeing concern.
        if (
            submission.feeling in {"need_support", "not_good"}
            and submission.is_resolved
            and submission.resolved_at
        ):
            recent_activity.append(
                {
                    "type": "resolved",
                    "title": "Wellbeing Alert Resolved",
                    "description": (
                        f"{senior_name}'s wellbeing concern "
                        "was marked as resolved."
                    ),
                    "senior": submission.senior,
                    "timestamp": submission.resolved_at,
                    "submission": submission,
                }
            )

    # --------------------------------------------------
    # SUPPORT REQUEST UPDATES
    # --------------------------------------------------

    support_requests = (
        SupportRequest.objects
        .filter(
            senior_id__in=assigned_senior_ids,
        )
        .select_related(
            "senior",
            "senior__app_user",
        )
        .order_by("-updated_at")[:10]
    )

    for support_request in support_requests:
        senior_name = support_request.senior.app_user.full_name

        recent_activity.append(
            {
                "type": "support",
                "title": "Support Request Updated",
                "description": (
                    f"{senior_name}'s support request is "
                    f"{support_request.get_status_display()}."
                ),
                "senior": support_request.senior,
                "timestamp": support_request.updated_at,
                "support_request": support_request,
            }
        )

    # --------------------------------------------------
    # VISIT REPORTS
    # --------------------------------------------------

    recent_reports = (
        VisitReport.objects
        .filter(
            visit__assignment__volunteer=volunteer_profile,
        )
        .select_related(
            "visit",
            "visit__assignment",
            "visit__assignment__senior",
            "visit__assignment__senior__app_user",
        )
        .order_by("-submitted_at")[:10]
    )

    for report in recent_reports:
        senior = report.visit.assignment.senior
        senior_name = senior.app_user.full_name

        recent_activity.append(
            {
                "type": "report",
                "title": "Visit Report Submitted",
                "description": (
                    f"A visit report for {senior_name} "
                    "was submitted."
                ),
                "senior": senior,
                "timestamp": report.submitted_at,
                "report": report,
            }
        )

    # Sort all activity types together by newest first.
    recent_activity.sort(
        key=lambda activity: activity["timestamp"],
        reverse=True,
    )

    # Dashboard only displays the five newest activities.
    recent_activity = recent_activity[:3]

    return render(
        request,
        "volunteerPortal/dashboard.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "upcoming_visits_count": upcoming_visits_count,
            "seniors_assigned_count": seniors_assigned_count,
            "reports_submitted_count": reports_submitted_count,
            "volunteer_hours": volunteer_hours,
            "todays_schedule": todays_schedule,
            "recent_activity": recent_activity,
        },
    )


# ==================================================
# MY SENIORS
# ==================================================

@login_required(login_url="login")
def my_seniors(request):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    # Get the search term from the URL.
    search_query = request.GET.get("search", "").strip()

    # Only show seniors actively assigned to this volunteer.
    assignments = (
        SeniorVolunteerAssignment.objects
        .filter(
            volunteer=volunteer_profile,
            active=True,
        )
        .select_related(
            "senior",
            "senior__app_user",
        )
        .order_by("senior__app_user__full_name")
    )

    # Search assigned seniors by name or senior number / ID.
    if search_query:
        if search_query.isdigit():
            assignments = assignments.filter(
                senior_id=int(search_query)
            )
        else:
            assignments = assignments.filter(
                senior__app_user__full_name__icontains=search_query
            )

    # Show a maximum of 5 seniors per page.
    paginator = Paginator(assignments, 5)

    assignments_page = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "volunteerPortal/my_seniors.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "assignments": assignments_page,
            "search_query": search_query,
        },
    )

# ==================================================
# INDIVIDUAL SENIOR PROFILE
# ==================================================

@login_required(login_url="login")
def volunteer_senior_detail(request, senior_id):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    assignment = get_object_or_404(
        SeniorVolunteerAssignment.objects.select_related(
            "senior",
            "senior__app_user",
        ),
        senior_id=senior_id,
        volunteer=volunteer_profile,
        active=True,
    )

    senior_profile = assignment.senior

    emergency_contact = getattr(
        senior_profile,
        "emergency_contact",
        None,
    )

    upcoming_visits = (
        ScheduledVisit.objects
        .filter(
            assignment=assignment,
            status="scheduled",
            visit_date__gte=date.today(),
        )
        .order_by(
            "visit_date",
            "start_time",
        )[:3]
    )

    previous_reports = (
        VisitReport.objects
        .filter(
            visit__assignment=assignment,
        )
        .select_related("visit")
        .order_by("-submitted_at")[:3]
    )

    return render(
        request,
        "volunteerPortal/senior_detail.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "assignment": assignment,
            "senior_profile": senior_profile,
            "senior_app_user": senior_profile.app_user,
            "emergency_contact": emergency_contact,
            "upcoming_visits": upcoming_visits,
            "previous_reports": previous_reports,
        },
    )


# ==================================================
# VOLUNTEER - SCHEDULE VISIT
# ==================================================

@login_required(login_url="login")
def volunteer_schedule_visit(request, senior_id):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    assignment = get_object_or_404(
        SeniorVolunteerAssignment.objects.select_related(
            "senior",
            "senior__app_user",
            "volunteer",
            "volunteer__app_user",
        ),
        senior_id=senior_id,
        volunteer=volunteer_profile,
        active=True,
    )

    availability_slots = (
        VolunteerAvailability.objects
        .filter(
            volunteer=volunteer_profile,
            date__gte=date.today(),
            available=True,
        )
        .order_by(
            "date",
            "start_time",
        )
    )

    if request.method == "POST":
        availability_id = request.POST.get("availability_id")
        visit_type = request.POST.get("visit_type")
        visit_purpose = request.POST.get("visit_purpose")
        support_types = request.POST.getlist("support_types")

        other_support_details = request.POST.get(
            "other_support_details",
            "",
        ).strip()

        estimated_duration = request.POST.get(
            "estimated_duration"
        )

        notes = request.POST.get(
            "notes",
            "",
        ).strip()

        if not availability_id:
            messages.error(
                request,
                "Please select an available date and time.",
            )
            return redirect(
                "volunteer_schedule_visit",
                senior_id=assignment.senior.pk,
            )

        if not visit_type or not visit_purpose:
            messages.error(
                request,
                "Please complete the visit details.",
            )
            return redirect(
                "volunteer_schedule_visit",
                senior_id=assignment.senior.pk,
            )

        availability = get_object_or_404(
            VolunteerAvailability,
            pk=availability_id,
            volunteer=volunteer_profile,
            available=True,
        )

        if availability.date < date.today():
            messages.error(
                request,
                "That availability slot is no longer available.",
            )
            return redirect(
                "volunteer_schedule_visit",
                senior_id=assignment.senior.pk,
            )

        try:
            duration_minutes = int(estimated_duration)

            if duration_minutes <= 0:
                raise ValueError

        except (TypeError, ValueError):
            duration_minutes = 60

        start_datetime = datetime.combine(
            availability.date,
            availability.start_time,
        )

        end_datetime = (
            start_datetime
            + timedelta(minutes=duration_minutes)
        )

        availability_end = datetime.combine(
            availability.date,
            availability.end_time,
        )

        if end_datetime > availability_end:
            messages.error(
                request,
                "The visit duration exceeds your available time.",
            )
            return redirect(
                "volunteer_schedule_visit",
                senior_id=assignment.senior.pk,
            )

        conflicting_visit = (
            ScheduledVisit.objects
            .filter(
                assignment__volunteer=volunteer_profile,
                visit_date=availability.date,
                status="scheduled",
                start_time__lt=end_datetime.time(),
                end_time__gt=availability.start_time,
            )
            .exists()
        )

        if conflicting_visit:
            messages.error(
                request,
                "You already have another visit during this time.",
            )
            return redirect(
                "volunteer_schedule_visit",
                senior_id=assignment.senior.pk,
            )

        with transaction.atomic():
            ScheduledVisit.objects.create(
                assignment=assignment,
                visit_type=visit_type,
                visit_purpose=visit_purpose,
                support_types=support_types,
                other_support_details=other_support_details,
                visit_date=availability.date,
                start_time=availability.start_time,
                end_time=end_datetime.time(),
                estimated_duration=duration_minutes,
                notes=notes,
                status="scheduled",
            )

        messages.success(
            request,
            (
                f"Visit with "
                f"{assignment.senior.app_user.full_name} "
                "has been scheduled successfully."
            ),
        )

        return redirect("volunteer_schedule")

    return render(
        request,
        "volunteerPortal/schedule_visit.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "assignment": assignment,
            "senior_profile": assignment.senior,
            "availability_slots": availability_slots,
            "visit_type_choices": ScheduledVisit.VISIT_TYPE_CHOICES,
            "visit_purpose_choices": (
                ScheduledVisit.VISIT_PURPOSE_CHOICES
            ),
        },
    )


# ==================================================
# VOLUNTEER PROFILE
# ==================================================

@login_required(login_url="login")
def volunteer_profile(request):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    today = date.today()

    # ==================================================
    # AGE
    # ==================================================

    age = (
        today.year
        - app_user.date_of_birth.year
        - (
            (today.month, today.day)
            <
            (
                app_user.date_of_birth.month,
                app_user.date_of_birth.day,
            )
        )
    )

    # ==================================================
    # DOCUMENTS
    # ==================================================

    documents = {
        document.document_type: document
        for document in volunteer_profile.documents.all()
    }

    identification_document = documents.get("identification")
    first_aid_document = documents.get("first_aid")
    background_document = documents.get("background")

    # ==================================================
    # SKILLS & INTERESTS
    # ==================================================

    custom_skills = []

    if volunteer_profile.skills_interests:
        custom_skills = [
            item.strip()
            for item in volunteer_profile.skills_interests.split(",")
            if item.strip()
        ]

    # ==================================================
    # RECENT VOLUNTEER ACTIVITIES
    # ==================================================

    recent_activities = []

    # --------------------------------------------------
    # CHECK-IN REPORTS SUBMITTED
    # --------------------------------------------------

    submitted_reports = (
        VisitReport.objects
        .filter(
            visit__assignment__volunteer=volunteer_profile,
        )
        .select_related(
            "visit",
            "visit__assignment",
            "visit__assignment__senior",
            "visit__assignment__senior__app_user",
        )
        .order_by("-submitted_at")[:10]
    )

    for report in submitted_reports:
        senior = report.visit.assignment.senior

        recent_activities.append(
            {
                "type": "report",
                "title": "Check-In Report Submitted",
                "description": (
                    f"Submitted a check-in report for "
                    f"{senior.app_user.full_name}."
                ),
                "senior": senior,
                "timestamp": report.submitted_at,
                "report": report,
            }
        )

    # --------------------------------------------------
    # COMPLETED VISITS WITHOUT REPORTS
    # --------------------------------------------------

    completed_visits = (
        ScheduledVisit.objects
        .filter(
            assignment__volunteer=volunteer_profile,
            status="completed",
            visit_report__isnull=True,
        )
        .select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
        )
        .order_by("-updated_at")[:10]
    )

    for visit in completed_visits:
        senior = visit.assignment.senior

        recent_activities.append(
            {
                "type": "completed",
                "title": "Visit Completed",
                "description": (
                    f"Completed a visit with "
                    f"{senior.app_user.full_name}."
                ),
                "senior": senior,
                "timestamp": visit.updated_at,
                "visit": visit,
            }
        )

    # --------------------------------------------------
    # SCHEDULED VISITS
    # --------------------------------------------------

    scheduled_visits = (
        ScheduledVisit.objects
        .filter(
            assignment__volunteer=volunteer_profile,
            status="scheduled",
        )
        .select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
        )
        .order_by("-created_at")[:10]
    )

    for visit in scheduled_visits:
        senior = visit.assignment.senior

        recent_activities.append(
            {
                "type": "scheduled",
                "title": "Visit Scheduled",
                "description": (
                    f"Scheduled a visit with "
                    f"{senior.app_user.full_name}."
                ),
                "senior": senior,
                "timestamp": visit.created_at,
                "visit": visit,
            }
        )

    # ==================================================
    # SORT AND LIMIT ACTIVITIES
    # ==================================================

    recent_activities.sort(
        key=lambda activity: activity["timestamp"],
        reverse=True,
    )

    recent_activities = recent_activities[:5]

    # ==================================================
    # RENDER PROFILE
    # ==================================================

    return render(
        request,
        "volunteerPortal/profile.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "age": age,
            "identification_document": identification_document,
            "first_aid_document": first_aid_document,
            "background_document": background_document,
            "custom_skills": custom_skills,
            "recent_activities": recent_activities,
        },
    )


# ==================================================
# EDIT VOLUNTEER PROFILE
# ==================================================

@login_required(login_url="login")
def edit_volunteer_profile(request):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    if request.method == "POST":
        account_form = VolunteerAccountEditForm(
            request.POST,
            request.FILES,
            instance=app_user,
            prefix="account",
        )

        profile_form = VolunteerProfileEditForm(
            request.POST,
            instance=volunteer_profile,
            prefix="profile",
        )

        if account_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                account_form.save()
                profile_form.save()

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )

            return redirect("volunteer_profile")

    else:
        account_form = VolunteerAccountEditForm(
            instance=app_user,
            prefix="account",
        )

        profile_form = VolunteerProfileEditForm(
            instance=volunteer_profile,
            prefix="profile",
        )

    return render(
        request,
        "volunteerPortal/edit_profile.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "account_form": account_form,
            "profile_form": profile_form,
        },
    )


# ==================================================
# VOLUNTEER DOCUMENT UPLOAD
# ==================================================

@login_required(login_url="login")
def upload_volunteer_document(request, document_type):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    allowed_types = {
        "identification": "NRIC / Identification Card",
        "first_aid": "First Aid Certificate",
        "background": "Background Appointment",
    }

    if document_type not in allowed_types:
        messages.error(
            request,
            "Invalid document type.",
        )
        return redirect("volunteer_profile")

    existing_document = (
        VolunteerDocument.objects
        .filter(
            volunteer=volunteer_profile,
            document_type=document_type,
        )
        .first()
    )

    if request.method == "POST":
        form = VolunteerDocumentUploadForm(
            request.POST,
            request.FILES,
            instance=existing_document,
        )

        if form.is_valid():
            document = form.save(commit=False)
            document.volunteer = volunteer_profile
            document.document_type = document_type
            document.save()

            messages.success(
                request,
                (
                    f"{allowed_types[document_type]} "
                    "uploaded successfully."
                ),
            )

            return redirect("volunteer_profile")

    else:
        form = VolunteerDocumentUploadForm(
            instance=existing_document,
        )

    return render(
        request,
        "volunteerPortal/upload_document.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "form": form,
            "document_type": document_type,
            "document_name": allowed_types[document_type],
            "existing_document": existing_document,
        },
    )


# ==================================================
# DELETE VOLUNTEER DOCUMENT
# ==================================================

@login_required(login_url="login")
def delete_volunteer_document(request, document_type):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    allowed_types = {
        "identification",
        "first_aid",
        "background",
    }

    if document_type not in allowed_types:
        messages.error(
            request,
            "Invalid document type.",
        )
        return redirect("volunteer_profile")

    document = (
        VolunteerDocument.objects
        .filter(
            volunteer=volunteer_profile,
            document_type=document_type,
        )
        .first()
    )

    if not document:
        messages.error(
            request,
            "That document could not be found.",
        )
        return redirect("volunteer_profile")

    if request.method == "POST":
        if document.file:
            document.file.delete(save=False)

        document.delete()

        messages.success(
            request,
            "Document deleted successfully.",
        )

    return redirect("volunteer_profile")


# ==================================================
# VOLUNTEER AVAILABILITY
# ==================================================

@login_required(login_url="login")
def volunteer_availability(request):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    requested_week = request.GET.get("week")

    if requested_week:
        try:
            week_start = datetime.strptime(
                requested_week,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            week_start = date.today()
    else:
        week_start = date.today()

    week_start -= timedelta(
        days=week_start.weekday()
    )

    week_end = week_start + timedelta(days=6)

    week_days = [
        week_start + timedelta(days=i)
        for i in range(7)
    ]

    previous_week = (
        week_start - timedelta(days=7)
    ).isoformat()

    next_week = (
        week_start + timedelta(days=7)
    ).isoformat()

    time_slots = []

    for hour in range(8, 18):
        start_value = f"{hour:02d}:00"
        end_value = f"{hour + 1:02d}:00"

        start_label = datetime.strptime(
            start_value,
            "%H:%M",
        ).strftime("%I:%M %p").lstrip("0")

        end_label = datetime.strptime(
            end_value,
            "%H:%M",
        ).strftime("%I:%M %p").lstrip("0")

        time_slots.append(
            {
                "start": start_value,
                "end": end_value,
                "label": f"{start_label} - {end_label}",
            }
        )

    if request.method == "POST":
        selected_slots_json = request.POST.get(
            "selected_slots",
            "[]",
        )

        try:
            selected_slots = json.loads(
                selected_slots_json
            )
        except json.JSONDecodeError:
            selected_slots = []

        with transaction.atomic():
            VolunteerAvailability.objects.filter(
                volunteer=volunteer_profile,
                date__range=(
                    week_start,
                    week_end,
                ),
            ).delete()

            for slot in selected_slots:
                VolunteerAvailability.objects.create(
                    volunteer=volunteer_profile,
                    date=slot["date"],
                    start_time=slot["start"],
                    end_time=slot["end"],
                    available=True,
                )

        messages.success(
            request,
            "Your availability has been saved successfully.",
        )

        return redirect(
            f"{request.path}?week={week_start.isoformat()}"
        )

    saved_availability = (
        VolunteerAvailability.objects
        .filter(
            volunteer=volunteer_profile,
            date__range=(
                week_start,
                week_end,
            ),
            available=True,
        )
    )

    saved_slot_keys = {
        (
            availability.date.isoformat()
            + "|"
            + availability.start_time.strftime("%H:%M")
        )
        for availability in saved_availability
    }

    availability_rows = []

    for slot in time_slots:
        cells = []

        for day in week_days:
            slot_key = (
                day.isoformat()
                + "|"
                + slot["start"]
            )

            cells.append(
                {
                    "date": day,
                    "start": slot["start"],
                    "end": slot["end"],
                    "selected": slot_key in saved_slot_keys,
                }
            )

        availability_rows.append(
            {
                "label": slot["label"],
                "cells": cells,
            }
        )

    return render(
        request,
        "volunteerPortal/availability.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "week_start": week_start,
            "week_end": week_end,
            "week_days": week_days,
            "previous_week": previous_week,
            "next_week": next_week,
            "availability_rows": availability_rows,
        },
    )


# ==================================================
# VOLUNTEER SCHEDULE
# ==================================================

@login_required(login_url="login")
def volunteer_schedule(request):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    requested_week = request.GET.get("week")

    if requested_week:
        try:
            week_start = datetime.strptime(
                requested_week,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            week_start = date.today()
    else:
        week_start = date.today()

    week_start -= timedelta(
        days=week_start.weekday()
    )

    week_end = week_start + timedelta(days=6)

    week_days = [
        week_start + timedelta(days=i)
        for i in range(7)
    ]

    previous_week = (
        week_start - timedelta(days=7)
    ).isoformat()

    next_week = (
        week_start + timedelta(days=7)
    ).isoformat()

    weekly_visits = (
        ScheduledVisit.objects
        .filter(
            assignment__volunteer=volunteer_profile,
            visit_date__range=(
                week_start,
                week_end,
            ),
        )
        .select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
            "assignment__volunteer",
            "assignment__volunteer__app_user",
        )
        .order_by(
            "visit_date",
            "start_time",
        )
    )

    visit_lookup = {}

    for visit in weekly_visits:
        visit_key = (
            visit.visit_date,
            visit.start_time.hour,
        )

        visit_lookup.setdefault(
            visit_key,
            [],
        ).append(visit)

    schedule_rows = []

    for hour in range(8, 19):
        start_label = datetime.strptime(
            f"{hour:02d}:00",
            "%H:%M",
        ).strftime("%I %p").lstrip("0")

        cells = []

        for day in week_days:
            visits_for_cell = visit_lookup.get(
                (day, hour),
                [],
            )

            primary_visit = (
                visits_for_cell[0]
                if visits_for_cell
                else None
            )

            cells.append(
                {
                    "date": day,
                    "visit": primary_visit,
                    "visits": visits_for_cell,
                }
            )

        schedule_rows.append(
            {
                "label": start_label,
                "hour": hour,
                "cells": cells,
            }
        )

    weekly_visit_count = weekly_visits.count()

    upcoming_visit_count = (
        weekly_visits
        .filter(status="scheduled")
        .count()
    )

    completed_visit_count = (
        weekly_visits
        .filter(status="completed")
        .count()
    )

    cancelled_visit_count = (
        weekly_visits
        .filter(status="cancelled")
        .count()
    )

    return render(
        request,
        "volunteerPortal/schedule.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "week_start": week_start,
            "week_end": week_end,
            "week_days": week_days,
            "previous_week": previous_week,
            "next_week": next_week,
            "schedule_rows": schedule_rows,
            "weekly_visits": weekly_visits,
            "weekly_visit_count": weekly_visit_count,
            "upcoming_visit_count": upcoming_visit_count,
            "completed_visit_count": completed_visit_count,
            "cancelled_visit_count": cancelled_visit_count,
        },
    )

# ==================================================
# VOLUNTEER VISIT DETAILS
# ==================================================

@login_required(login_url="login")
def volunteer_visit_detail(request, visit_id):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    visit = get_object_or_404(
        ScheduledVisit.objects.select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
        ),
        pk=visit_id,
        assignment__volunteer=volunteer_profile,
    )

    senior = visit.assignment.senior

    # Emergency contact may not exist for every senior.
    try:
        emergency_contact = senior.emergency_contact
    except EmergencyContact.DoesNotExist:
        emergency_contact = None

    # Existing report, if one has already been submitted.
    try:
        visit_report = visit.visit_report
    except VisitReport.DoesNotExist:
        visit_report = None

    return render(
        request,
        "volunteerPortal/visit_detail.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "visit": visit,
            "senior": senior,
            "emergency_contact": emergency_contact,
            "visit_report": visit_report,
        },
    )


# ==================================================
# VOLUNTEER CHECK-IN REPORTS
# ==================================================

@login_required(login_url="login")
def volunteer_check_in_reports(request):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    visits_to_report = (
        ScheduledVisit.objects
        .filter(
            assignment__volunteer=volunteer_profile,
            status="scheduled",
            visit_date__lte=date.today(),
            visit_report__isnull=True,
        )
        .select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
        )
        .order_by(
            "-visit_date",
            "-start_time",
        )
    )

    submitted_reports = (
        VisitReport.objects
        .filter(
            visit__assignment__volunteer=volunteer_profile,
        )
        .select_related(
            "visit",
            "visit__assignment",
            "visit__assignment__senior",
            "visit__assignment__senior__app_user",
        )
        .order_by("-submitted_at")
    )

    selected_status = request.GET.get(
        "status",
        "all",
    )

    if selected_status in {
        "good",
        "okay",
        "concern",
    }:
        submitted_reports = submitted_reports.filter(
            wellbeing_status=selected_status
        )

    all_reports = (
        VisitReport.objects
        .filter(
            visit__assignment__volunteer=volunteer_profile,
        )
    )

    total_reports = all_reports.count()

    good_reports = (
        all_reports
        .filter(wellbeing_status="good")
        .count()
    )

    attention_reports = (
        all_reports
        .filter(wellbeing_status="okay")
        .count()
    )

    concern_reports = (
        all_reports
        .filter(wellbeing_status="concern")
        .count()
    )

    paginator = Paginator(
        submitted_reports,
        5,
    )

    reports_page = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "volunteerPortal/check_in_reports.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "visits_to_report": visits_to_report,
            "submitted_reports": reports_page,
            "total_reports": total_reports,
            "good_reports": good_reports,
            "attention_reports": attention_reports,
            "concern_reports": concern_reports,
            "selected_status": selected_status,
        },
    )


# ==================================================
# SUBMIT VISIT REPORT
# ==================================================

@login_required(login_url="login")
def submit_visit_report(request, visit_id):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    visit = get_object_or_404(
        ScheduledVisit.objects.select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
            "assignment__volunteer",
            "assignment__volunteer__app_user",
        ),
        pk=visit_id,
        assignment__volunteer=volunteer_profile,
    )

    if visit.status == "cancelled":
        messages.error(
            request,
            "A report cannot be submitted for a cancelled visit.",
        )
        return redirect("volunteer_check_in_reports")

    if visit.visit_date > date.today():
        messages.error(
            request,
            "A report cannot be submitted before the visit date.",
        )
        return redirect("volunteer_check_in_reports")

    existing_report = (
        VisitReport.objects
        .filter(visit=visit)
        .first()
    )

    if request.method == "POST":
        form = VisitReportForm(
            request.POST,
            instance=existing_report,
        )

        if form.is_valid():
            with transaction.atomic():
                report = form.save(commit=False)
                report.visit = visit
                report.save()

                visit.status = "completed"
                visit.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            messages.success(
                request,
                "Your visit report has been submitted successfully.",
            )

            return redirect("volunteer_check_in_reports")

    else:
        form = VisitReportForm(
            instance=existing_report,
        )

    return render(
        request,
        "volunteerPortal/submit_visit_report.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "visit": visit,
            "form": form,
            "existing_report": existing_report,
        },
    )


# ==================================================
# VIEW SUBMITTED REPORT
# ==================================================

@login_required(login_url="login")
def volunteer_view_report(request, report_id):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    report = get_object_or_404(
        VisitReport.objects.select_related(
            "visit",
            "visit__assignment",
            "visit__assignment__senior",
            "visit__assignment__senior__app_user",
            "visit__assignment__volunteer",
            "visit__assignment__volunteer__app_user",
        ),
        pk=report_id,
        visit__assignment__volunteer=volunteer_profile,
    )

    return render(
        request,
        "volunteerPortal/view_visit_report.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "report": report,
            "visit": report.visit,
        },
    )


# ==================================================
# VOLUNTEER ALERTS
# ==================================================

@login_required(login_url="login")
def volunteer_alerts(request):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    wellbeing_submissions = (
        WellbeingSubmission.objects
        .filter(
            senior__volunteer_assignments__volunteer=volunteer_profile,
            senior__volunteer_assignments__active=True,
            feeling__in=[
                "need_support",
                "not_good",
            ],
            is_resolved=False,
        )
        .select_related(
            "senior",
            "senior__app_user",
        )
        .distinct()
        .order_by("-submitted_at")
    )

    alerts = []

    for submission in wellbeing_submissions:
        if submission.feeling == "need_support":
            priority = "high"
            priority_label = "High Priority"
        else:
            priority = "medium"
            priority_label = "Medium Priority"

        alerts.append(
            {
                "submission": submission,
                "senior": submission.senior,
                "senior_name": (
                    submission.senior.app_user.full_name
                ),
                "feeling": submission.get_feeling_display(),
                "notes": submission.notes,
                "submitted_at": submission.submitted_at,
                "priority": priority,
                "priority_label": priority_label,
            }
        )

    total_alerts = len(alerts)

    high_priority_count = sum(
        alert["priority"] == "high"
        for alert in alerts
    )

    medium_priority_count = sum(
        alert["priority"] == "medium"
        for alert in alerts
    )

    return render(
        request,
        "volunteerPortal/alerts.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "alerts": alerts,
            "total_alerts": total_alerts,
            "high_priority_count": high_priority_count,
            "medium_priority_count": medium_priority_count,
        },
    )


# ==================================================
# VOLUNTEER ALERT DETAIL
# ==================================================

@login_required(login_url="login")
def volunteer_alert_detail(request, submission_id):
    app_user, volunteer_profile, redirect_response = (
        get_volunteer_context(request)
    )

    if redirect_response:
        return redirect_response

    submission = get_object_or_404(
        WellbeingSubmission.objects.select_related(
            "senior",
            "senior__app_user",
        ),
        pk=submission_id,
        senior__volunteer_assignments__volunteer=volunteer_profile,
        senior__volunteer_assignments__active=True,
    )

    return render(
        request,
        "volunteerPortal/alert_detail.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "submission": submission,
            "senior": submission.senior,
        },
    )
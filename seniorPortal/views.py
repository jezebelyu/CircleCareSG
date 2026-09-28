from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from accounts.models import (
    AppUser,
    EmergencyContact,
    SeniorProfile,
    SeniorVolunteerAssignment,
)
from adminPortal.models import ScheduledVisit

from .forms import (
    EmergencyContactEditForm,
    SeniorAccountEditForm,
    SeniorProfileEditForm,
    SupportRequestDetailsForm,
    SupportSelectionForm,
    WellbeingSubmissionForm,
)
from .models import SupportRequest, WellbeingSubmission


# Senior dashboard

@login_required(login_url="login")
def senior_dashboard(request):
    try:
        app_user = request.user.app_profile
    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "senior":
        messages.error(
            request,
            "You do not have permission to access the Senior Portal.",
        )
        return redirect("home")

    try:
        senior_profile = app_user.senior_profile
    except SeniorProfile.DoesNotExist:
        messages.error(
            request,
            "Your senior profile could not be found.",
        )
        return redirect("home")

    try:
        emergency_contact = senior_profile.emergency_contact
    except EmergencyContact.DoesNotExist:
        emergency_contact = None

    # Get the senior's current volunteer assignment.
    assignment = (
        SeniorVolunteerAssignment.objects
        .filter(
            senior=senior_profile,
            active=True,
        )
        .select_related(
            "volunteer",
            "volunteer__app_user",
        )
        .order_by("-assigned_at")
        .first()
    )

    # Show the nearest scheduled visit, if one exists.
    upcoming_visit = None

    if assignment:
        upcoming_visit = (
            ScheduledVisit.objects
            .filter(
                assignment=assignment,
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

    # Show the most recent request that is still active.
    active_support_request = (
        SupportRequest.objects
        .filter(
            senior=senior_profile,
            status__in=[
                "pending",
                "reviewing",
                "approved",
                "ongoing",
            ],
        )
        .order_by("-submitted_at")
        .first()
    )

    return render(
        request,
        "seniorPortal/dashboard.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "emergency_contact": emergency_contact,
            "assignment": assignment,
            "upcoming_visit": upcoming_visit,
            "active_support_request": active_support_request,
        },
    )


# Senior profile

@login_required(login_url="login")
def senior_profile(request):
    try:
        app_user = request.user.app_profile
    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "senior":
        messages.error(
            request,
            "You do not have permission to access the Senior Portal.",
        )
        return redirect("home")

    try:
        senior_profile = app_user.senior_profile
    except SeniorProfile.DoesNotExist:
        messages.error(
            request,
            "Your senior profile could not be found.",
        )
        return redirect("senior_dashboard")

    try:
        emergency_contact = senior_profile.emergency_contact
    except EmergencyContact.DoesNotExist:
        emergency_contact = None

    return render(
        request,
        "seniorPortal/profile.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "emergency_contact": emergency_contact,
        },
    )


# Edit senior profile

@login_required(login_url="login")
def edit_senior_profile(request):
    try:
        app_user = request.user.app_profile
    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "senior":
        messages.error(
            request,
            "You do not have permission to access this page.",
        )
        return redirect("home")

    try:
        senior_profile = app_user.senior_profile
    except SeniorProfile.DoesNotExist:
        messages.error(
            request,
            "Your senior profile could not be found.",
        )
        return redirect("senior_dashboard")

    try:
        emergency_contact = senior_profile.emergency_contact
    except EmergencyContact.DoesNotExist:
        emergency_contact = None

    if request.method == "POST":
        account_form = SeniorAccountEditForm(
            request.POST,
            request.FILES,
            instance=app_user,
            prefix="account",
        )
        profile_form = SeniorProfileEditForm(
            request.POST,
            instance=senior_profile,
            prefix="profile",
        )
        emergency_form = EmergencyContactEditForm(
            request.POST,
            instance=emergency_contact,
            prefix="emergency",
        )

        if (
            account_form.is_valid()
            and profile_form.is_valid()
            and emergency_form.is_valid()
        ):
            with transaction.atomic():
                account_form.save()
                profile_form.save()

                saved_contact = emergency_form.save(commit=False)
                saved_contact.senior = senior_profile
                saved_contact.save()

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )
            return redirect("senior_profile")

    else:
        account_form = SeniorAccountEditForm(
            instance=app_user,
            prefix="account",
        )
        profile_form = SeniorProfileEditForm(
            instance=senior_profile,
            prefix="profile",
        )
        emergency_form = EmergencyContactEditForm(
            instance=emergency_contact,
            prefix="emergency",
        )

    return render(
        request,
        "seniorPortal/edit_profile.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "emergency_contact": emergency_contact,
            "account_form": account_form,
            "profile_form": profile_form,
            "emergency_form": emergency_form,
        },
    )


# Wellbeing check-in

@login_required(login_url="login")
def senior_wellbeing(request):
    try:
        app_user = request.user.app_profile
    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "senior":
        messages.error(
            request,
            "You do not have permission to access this page.",
        )
        return redirect("home")

    try:
        senior_profile = app_user.senior_profile
    except SeniorProfile.DoesNotExist:
        messages.error(
            request,
            "Your senior profile could not be found.",
        )
        return redirect("senior_dashboard")

    if request.method == "POST":
        form = WellbeingSubmissionForm(request.POST)

        if form.is_valid():
            wellbeing = form.save(commit=False)
            wellbeing.senior = senior_profile
            wellbeing.save()

            messages.success(
                request,
                "Your wellbeing update has been submitted successfully.",
            )
            return redirect("check_in_history")

    else:
        form = WellbeingSubmissionForm()

    return render(
        request,
        "seniorPortal/wellbeing.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "form": form,
        },
    )


# Check-in history

@login_required(login_url="login")
def check_in_history(request):
    try:
        app_user = request.user.app_profile
    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "senior":
        messages.error(
            request,
            "You do not have permission to access the Senior Portal.",
        )
        return redirect("home")

    try:
        senior_profile = app_user.senior_profile
    except SeniorProfile.DoesNotExist:
        messages.error(
            request,
            "Your senior profile could not be found.",
        )
        return redirect("senior_dashboard")

    wellbeing_submissions = (
        WellbeingSubmission.objects
        .filter(senior=senior_profile)
        .order_by("-submitted_at")
    )

    return render(
        request,
        "seniorPortal/check_in_history.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "wellbeing_submissions": wellbeing_submissions,
        },
    )


# Assigned volunteer

@login_required(login_url="login")
def senior_volunteer(request):
    try:
        app_user = request.user.app_profile
    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "senior":
        messages.error(
            request,
            "You do not have permission to access the Senior Portal.",
        )
        return redirect("home")

    try:
        senior_profile = app_user.senior_profile
    except SeniorProfile.DoesNotExist:
        messages.error(
            request,
            "Your senior profile could not be found.",
        )
        return redirect("senior_dashboard")

    assignment = (
        SeniorVolunteerAssignment.objects
        .filter(
            senior=senior_profile,
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

    assigned_volunteer = assignment.volunteer if assignment else None

    upcoming_visit = None

    if assignment:
        upcoming_visit = (
            ScheduledVisit.objects
            .filter(
                assignment=assignment,
                status="scheduled",
                visit_date__gte=date.today(),
            )
            .order_by(
                "visit_date",
                "start_time",
            )
            .first()
        )

    return render(
        request,
        "seniorPortal/my_volunteer.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "assignment": assignment,
            "assigned_volunteer": assigned_volunteer,
            "upcoming_visit": upcoming_visit,
        },
    )


# Support request history

@login_required(login_url="login")
def support_request_history(request):
    try:
        app_user = request.user.app_profile
    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "senior":
        messages.error(
            request,
            "You do not have permission to access this page.",
        )
        return redirect("home")

    try:
        senior_profile = app_user.senior_profile
    except SeniorProfile.DoesNotExist:
        messages.error(
            request,
            "Your senior profile could not be found.",
        )
        return redirect("senior_dashboard")

    support_requests = (
        SupportRequest.objects
        .filter(senior=senior_profile)
        .order_by("-submitted_at")
    )

    return render(
        request,
        "seniorPortal/support_request_history.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "support_requests": support_requests,
        },
    )


# Support request - Step 1

@login_required(login_url="login")
def support_request_select(request):
    try:
        app_user = request.user.app_profile
        senior_profile = app_user.senior_profile
    except (
        AppUser.DoesNotExist,
        SeniorProfile.DoesNotExist,
    ):
        messages.error(
            request,
            "Your senior profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "senior":
        messages.error(
            request,
            "You do not have permission to access this page.",
        )
        return redirect("home")

    initial_data = {
        "support_types": request.session.get(
            "selected_support_types",
            [],
        ),
    }

    if request.method == "POST":
        form = SupportSelectionForm(request.POST)

        if form.is_valid():
            request.session["selected_support_types"] = (
                form.cleaned_data["support_types"]
            )
            request.session.modified = True

            return redirect("support_request_details")

    else:
        form = SupportSelectionForm(initial=initial_data)

    return render(
        request,
        "seniorPortal/support_request_select.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "form": form,
        },
    )


# Support request - Step 2

@login_required(login_url="login")
def support_request_details(request):
    try:
        app_user = request.user.app_profile
        senior_profile = app_user.senior_profile
    except (
        AppUser.DoesNotExist,
        SeniorProfile.DoesNotExist,
    ):
        messages.error(
            request,
            "Your senior profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "senior":
        messages.error(
            request,
            "You do not have permission to access this page.",
        )
        return redirect("home")

    selected_support_types = request.session.get(
        "selected_support_types"
    )

    if not selected_support_types:
        messages.error(
            request,
            "Please select at least one support type.",
        )
        return redirect("support_request_select")

    support_labels = dict(SupportRequest.SUPPORT_TYPE_CHOICES)

    selected_support_labels = [
        support_labels.get(value, value)
        for value in selected_support_types
    ]

    if request.method == "POST":
        form = SupportRequestDetailsForm(request.POST)

        if form.is_valid():
            other_details = (
                form.cleaned_data
                .get("other_support_details", "")
                .strip()
            )

            if (
                "other" in selected_support_types
                and not other_details
            ):
                form.add_error(
                    "other_support_details",
                    "Please describe the other assistance needed.",
                )

            else:
                SupportRequest.objects.create(
                    senior=senior_profile,
                    support_types=selected_support_types,
                    other_support_details=other_details,
                    requested_date=form.cleaned_data[
                        "requested_date"
                    ],
                    requested_time=form.cleaned_data[
                        "requested_time"
                    ],
                    additional_notes=form.cleaned_data[
                        "additional_notes"
                    ],
                )

                request.session.pop(
                    "selected_support_types",
                    None,
                )
                request.session.modified = True

                messages.success(
                    request,
                    "Your support request has been submitted successfully.",
                )
                return redirect("support_request_history")

    else:
        form = SupportRequestDetailsForm()

    return render(
        request,
        "seniorPortal/support_request_details.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "form": form,
            "selected_support_types": selected_support_types,
            "selected_support_labels": selected_support_labels,
        },
    )
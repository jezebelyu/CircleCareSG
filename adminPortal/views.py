from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import (
    AppUser,
    EmergencyContact,
    SeniorProfile,
    SeniorVolunteerAssignment,
    VolunteerProfile,
)

from seniorPortal.models import (
    SupportRequest,
    WellbeingSubmission,
)

from volunteerPortal.models import (
    VisitReport,
    VolunteerAvailability,
)

from .forms import (
    AdminAddSeniorForm,
    AdminAddVolunteerForm,
    AdminEmergencyContactForm,
    AdminProfileForm,
    AdminSeniorAccountForm,
    AdminSeniorProfileForm,
    AdminVolunteerAccountForm,
    AdminVolunteerProfileForm,
)

from .models import ScheduledVisit

@login_required(login_url="login")
def admin_dashboard(request):
    
    print("ADMIN DASHBOARD DEBUG")
    print("USER:", request.user)
    print("USER ID:", request.user.id)
    print("AUTHENTICATED:", request.user.is_authenticated)
    
    # ==================================================
    # ADMIN ACCESS
    # ==================================================

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")

    today = date.today()


    # ==================================================
    # TOTAL USERS
    # ==================================================

    total_seniors = SeniorProfile.objects.count()
    total_volunteers = VolunteerProfile.objects.count()


    # ==================================================
    # VISIT STATISTICS
    # ==================================================

    total_visits = ScheduledVisit.objects.count()

    completed_check_ins = (
        ScheduledVisit.objects
        .filter(status="completed")
        .count()
    )

    pending_check_ins = (
        ScheduledVisit.objects
        .filter(status="scheduled")
        .count()
    )

    missed_check_ins = (
        ScheduledVisit.objects
        .filter(status="cancelled")
        .count()
    )


    # ==================================================
    # CHECK-IN RATE
    #
    # Only visits due today or earlier are included.
    # Future visits do not reduce the completion rate.
    # ==================================================

    due_visits = (
        ScheduledVisit.objects
        .filter(visit_date__lte=today)
        .count()
    )

    completed_due_visits = (
        ScheduledVisit.objects
        .filter(
            status="completed",
            visit_date__lte=today,
        )
        .count()
    )

    if due_visits > 0:
        check_in_rate = round(
            (completed_due_visits / due_visits) * 100
        )
    else:
        check_in_rate = 0


    # ==================================================
    # VISITS BY TYPE
    #
    # Blue  = Home Visit
    # Green = Phone Call
    # ==================================================

    home_visit_count = (
        ScheduledVisit.objects
        .filter(visit_type="home_visit")
        .count()
    )

    phone_call_count = (
        ScheduledVisit.objects
        .filter(visit_type="phone_call")
        .count()
    )

    visit_type_total = (
        home_visit_count + phone_call_count
    )

    if visit_type_total > 0:
        home_visit_percent = round(
            (home_visit_count / visit_type_total) * 100,
            2,
        )

        phone_call_percent = round(
            (phone_call_count / visit_type_total) * 100,
            2,
        )

    else:
        home_visit_percent = 0
        phone_call_percent = 0


    # ==================================================
    # VISIT OVERVIEW — MONTHLY PERIOD
    # ==================================================

    period = request.GET.get(
        "period",
        "current",
    )

    current_month_start = today.replace(day=1)

    if period == "last":
        previous_month_end = (
            current_month_start
            - timedelta(days=1)
        )

        selected_year = previous_month_end.year
        selected_month = previous_month_end.month

        visit_period_label = (
            previous_month_end.strftime("%B %Y")
        )

    else:
        period = "current"

        selected_year = today.year
        selected_month = today.month

        visit_period_label = today.strftime(
            "%B %Y"
        )


    # ==================================================
    # MONTHLY VISITS
    # ==================================================

    monthly_visits = (
        ScheduledVisit.objects
        .filter(
            visit_date__year=selected_year,
            visit_date__month=selected_month,
        )
    )

    monthly_completed = (
        monthly_visits
        .filter(status="completed")
        .count()
    )

    monthly_scheduled = (
        monthly_visits
        .filter(status="scheduled")
        .count()
    )

    monthly_cancelled = (
        monthly_visits
        .filter(status="cancelled")
        .count()
    )

    monthly_total = monthly_visits.count()


    # ==================================================
    # VISIT OVERVIEW BAR HEIGHTS
    # ==================================================

    max_monthly_count = max(
        monthly_completed,
        monthly_scheduled,
        monthly_cancelled,
        1,
    )

    completed_percent = round(
        (monthly_completed / max_monthly_count) * 100
    )

    scheduled_percent = round(
        (monthly_scheduled / max_monthly_count) * 100
    )

    cancelled_percent = round(
        (monthly_cancelled / max_monthly_count) * 100
    )


    # ==================================================
    # RECENT ACTIVITIES
    # ==================================================

    recent_activities = []


    # ==================================================
    # RECENT VISIT REPORTS
    # ==================================================

    recent_reports = (
        VisitReport.objects
        .select_related(
            "visit",
            "visit__assignment",
            "visit__assignment__senior",
            "visit__assignment__senior__app_user",
            "visit__assignment__volunteer",
            "visit__assignment__volunteer__app_user",
        )
        .order_by("-submitted_at")[:5]
    )

    for report in recent_reports:
        senior_name = (
            report.visit
            .assignment
            .senior
            .app_user
            .full_name
        )

        volunteer_name = (
            report.visit
            .assignment
            .volunteer
            .app_user
            .full_name
        )

        recent_activities.append(
            {
                "title": "Visit Report Submitted",

                "description": (
                    f"{volunteer_name} submitted a report "
                    f"for {senior_name}."
                ),

                "time": report.submitted_at,
                "sort_time": report.submitted_at,
            }
        )


    # ==================================================
    # RECENT SUPPORT REQUESTS
    # ==================================================

    recent_support_requests = (
        SupportRequest.objects
        .select_related(
            "senior",
            "senior__app_user",
        )
        .order_by("-submitted_at")[:5]
    )

    for support_request in recent_support_requests:
        senior_name = (
            support_request
            .senior
            .app_user
            .full_name
        )

        recent_activities.append(
            {
                "title": "Support Request Submitted",

                "description": (
                    f"{senior_name} submitted a new "
                    f"support request."
                ),

                "time": support_request.submitted_at,
                "sort_time": support_request.submitted_at,
            }
        )


    # ==================================================
    # SORT RECENT ACTIVITIES
    # ==================================================

    recent_activities = sorted(
        recent_activities,
        key=lambda item: item["sort_time"],
        reverse=True,
    )[:5]


    # ==================================================
    # RENDER DASHBOARD
    # ==================================================

    context = {
        "app_user": app_user,

        # Summary cards
        "total_seniors": total_seniors,
        "total_volunteers": total_volunteers,
        "total_visits": total_visits,
        "check_in_rate": check_in_rate,

        # Check-in statistics
        "completed_check_ins": completed_check_ins,
        "pending_check_ins": pending_check_ins,
        "missed_check_ins": missed_check_ins,

        # Visit by type
        "home_visit_count": home_visit_count,
        "phone_call_count": phone_call_count,
        "home_visit_percent": home_visit_percent,
        "phone_call_percent": phone_call_percent,

        # Recent activities
        "recent_activities": recent_activities,

        # Selected period
        "period": period,
        "visit_period_label": visit_period_label,

        # Monthly visit overview
        "monthly_total": monthly_total,
        "monthly_completed": monthly_completed,
        "monthly_scheduled": monthly_scheduled,
        "monthly_cancelled": monthly_cancelled,

        # Bar chart percentages
        "completed_percent": completed_percent,
        "scheduled_percent": scheduled_percent,
        "cancelled_percent": cancelled_percent,
    }

    return render(
        request,
        "adminPortal/dashboard.html",
        context,
    )

# ==================================================
# ADMIN - ALL SENIORS
# ==================================================

@login_required(login_url="login")
def admin_seniors(request):

    # ==================================================
    # ADMIN ACCESS
    # ==================================================

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")

    today = date.today()


    # ==================================================
    # SEARCH
    # ==================================================

    search_query = request.GET.get(
        "search",
        "",
    ).strip()

    seniors = (
        SeniorProfile.objects
        .select_related(
            "app_user",
            "app_user__user",
        )
        .order_by(
            "app_user__full_name"
        )
    )

    if search_query:
        seniors = seniors.filter(
            app_user__full_name__icontains=search_query
        )


    # ==================================================
    # PREPARE SENIOR DISPLAY DATA
    # ==================================================

    senior_rows = []

    for senior in seniors:

        birth_date = senior.app_user.date_of_birth

        age = (
            today.year
            - birth_date.year
            - (
                (today.month, today.day)
                <
                (
                    birth_date.month,
                    birth_date.day,
                )
            )
        )


        # ==================================================
        # LAST COMPLETED VISIT
        # ==================================================

        last_visit = (
            ScheduledVisit.objects
            .filter(
                assignment__senior=senior,
                status="completed",
            )
            .order_by(
                "-visit_date",
                "-start_time",
            )
            .first()
        )


        # ==================================================
        # NEXT UPCOMING VISIT
        # ==================================================

        next_visit = (
            ScheduledVisit.objects
            .filter(
                assignment__senior=senior,
                status="scheduled",
                visit_date__gte=today,
            )
            .order_by(
                "visit_date",
                "start_time",
            )
            .first()
        )


        senior_rows.append(
            {
                "profile": senior,

                "senior_id": (
                    f"SEN-{senior.pk:04d}"
                ),

                "age": age,

                "status": (
                    "active"
                    if senior.app_user.user.is_active
                    else "inactive"
                ),

                "last_visit": (
                    last_visit.visit_date
                    if last_visit
                    else None
                ),

                "next_visit": (
                    next_visit.visit_date
                    if next_visit
                    else None
                ),
            }
        )


    # ==================================================
    # SUMMARY COUNTS
    # ==================================================

    total_seniors = SeniorProfile.objects.count()

    active_seniors = (
        SeniorProfile.objects
        .filter(
            app_user__user__is_active=True
        )
        .count()
    )

    inactive_seniors = (
        SeniorProfile.objects
        .filter(
            app_user__user__is_active=False
        )
        .count()
    )

    upcoming_visits = (
        ScheduledVisit.objects
        .filter(
            status="scheduled",
            visit_date__gte=today,
        )
        .count()
    )


    # ==================================================
    # RENDER PAGE
    # ==================================================

    context = {
        "app_user": app_user,

        "senior_rows": senior_rows,

        "total_seniors": total_seniors,
        "active_seniors": active_seniors,
        "inactive_seniors": inactive_seniors,
        "upcoming_visits": upcoming_visits,

        "search_query": search_query,
    }

    return render(
        request,
        "adminPortal/seniors.html",
        context,
    )

# ==================================================
# ADMIN - ADD SENIOR
# ==================================================

@login_required(login_url="login")
def admin_add_senior(request):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


    if request.method == "POST":

        form = AdminAddSeniorForm(
            request.POST
        )

        if form.is_valid():

            email = (
                form.cleaned_data["email"]
                .strip()
                .lower()
            )

            nric_fin = (
                form.cleaned_data["nric_fin"]
                .strip()
                .upper()
            )

            try:

                with transaction.atomic():

                    # ==========================================
                    # DJANGO USER
                    # ==========================================

                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=form.cleaned_data["password"],
                    )


                    # ==========================================
                    # CIRCLECARESG APP USER
                    # ==========================================

                    new_app_user = AppUser.objects.create(
                        user=user,
                        account_type="senior",
                        full_name=form.cleaned_data[
                            "full_name"
                        ].strip(),
                        nric_fin=nric_fin,
                        mobile_number=form.cleaned_data[
                            "mobile_number"
                        ].strip(),
                        date_of_birth=form.cleaned_data[
                            "date_of_birth"
                        ],
                    )


                    # ==========================================
                    # SENIOR PROFILE
                    # ==========================================

                    senior_profile = SeniorProfile.objects.create(
                        app_user=new_app_user,

                        address=form.cleaned_data[
                            "address"
                        ].strip(),

                        postal_code=form.cleaned_data[
                            "postal_code"
                        ].strip(),

                        unit_number=form.cleaned_data.get(
                            "unit_number",
                            "",
                        ).strip(),

                        preferred_language=form.cleaned_data[
                            "preferred_language"
                        ],

                        regular_check_ins=form.cleaned_data.get(
                            "regular_check_ins",
                            False,
                        ),

                        mobility_assistance=form.cleaned_data.get(
                            "mobility_assistance",
                            False,
                        ),

                        meal_assistance=form.cleaned_data.get(
                            "meal_assistance",
                            False,
                        ),

                        emotional_support=form.cleaned_data.get(
                            "emotional_support",
                            False,
                        ),

                        medical_assistance=form.cleaned_data.get(
                            "medical_assistance",
                            False,
                        ),

                        other_support=form.cleaned_data.get(
                            "other_support",
                            "",
                        ).strip(),

                        religion=form.cleaned_data.get(
                            "religion",
                            "",
                        ).strip(),

                        medical_conditions=form.cleaned_data.get(
                            "medical_conditions",
                            "",
                        ).strip(),

                        allergies=form.cleaned_data.get(
                            "allergies",
                            "",
                        ).strip(),
                    )


                    # ==========================================
                    # EMERGENCY CONTACT
                    # ==========================================

                    EmergencyContact.objects.create(
                        senior=senior_profile,

                        full_name=form.cleaned_data[
                            "emergency_full_name"
                        ].strip(),

                        relationship=form.cleaned_data[
                            "emergency_relationship"
                        ].strip(),

                        mobile_number=form.cleaned_data[
                            "emergency_mobile_number"
                        ].strip(),
                    )


                messages.success(
                    request,
                    (
                        "Senior account created successfully. "
                        "The senior can now log in using their "
                        "email address and password."
                    ),
                )

                return redirect(
                    "admin_seniors"
                )


            except Exception:

                messages.error(
                    request,
                    (
                        "The senior account could not be created. "
                        "Please check the information and try again."
                    ),
                )

    else:

        form = AdminAddSeniorForm()


    return render(
        request,
        "adminPortal/add_senior.html",
        {
            "app_user": app_user,
            "form": form,
        },
    )

# ==================================================
# ADMIN - INDIVIDUAL SENIOR
# ==================================================

@login_required(login_url="login")
def admin_senior_detail(request, senior_id):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")

    senior_profile = get_object_or_404(
        SeniorProfile.objects.select_related(
            "app_user",
            "app_user__user",
        ),
        pk=senior_id,
    )

    try:
        emergency_contact = (
            senior_profile.emergency_contact
        )

    except EmergencyContact.DoesNotExist:
        emergency_contact = None

    # Calculate age
    birth_date = senior_profile.app_user.date_of_birth
    today = date.today()

    age = (
        today.year
        - birth_date.year
        - (
            (today.month, today.day)
            <
            (
                birth_date.month,
                birth_date.day,
            )
        )
    )
    
    # ==================================================
    # UPCOMING VISITS
    # ==================================================

    upcoming_visits = (
        ScheduledVisit.objects
        .filter(
            assignment__senior=senior_profile,
            status="scheduled",
            visit_date__gte=today,
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


    # ==================================================
    # PREVIOUS REPORTS
    # ==================================================

    previous_reports = (
        VisitReport.objects
        .filter(
            visit__assignment__senior=senior_profile,
        )
        .select_related(
            "visit",
            "visit__assignment",
            "visit__assignment__volunteer",
            "visit__assignment__volunteer__app_user",
        )
        .order_by(
            "-submitted_at"
        )[:3]
    )

    return render(
        request,
        "adminPortal/senior_detail.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "senior_app_user": senior_profile.app_user,
            "emergency_contact": emergency_contact,
            "age": age,

            "upcoming_visits": upcoming_visits,
            "previous_reports": previous_reports,
        },
    )

# ==================================================
# ADMIN - EDIT SENIOR
# ==================================================

@login_required(login_url="login")
def admin_edit_senior(request, senior_id):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")

    senior_profile = get_object_or_404(
        SeniorProfile.objects.select_related(
            "app_user",
        ),
        pk=senior_id,
    )

    senior_app_user = senior_profile.app_user

    try:
        emergency_contact = (
            senior_profile.emergency_contact
        )

    except EmergencyContact.DoesNotExist:
        emergency_contact = None

    if request.method == "POST":

        account_form = AdminSeniorAccountForm(
            request.POST,
            instance=senior_app_user,
            prefix="account",
        )

        profile_form = AdminSeniorProfileForm(
            request.POST,
            instance=senior_profile,
            prefix="profile",
        )

        emergency_form = AdminEmergencyContactForm(
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

                saved_contact = emergency_form.save(
                    commit=False
                )

                saved_contact.senior = senior_profile
                saved_contact.save()

            messages.success(
                request,
                "Senior information updated successfully.",
            )

            return redirect(
                "admin_senior_detail",
                senior_id=senior_profile.pk,
            )

    else:
        account_form = AdminSeniorAccountForm(
            instance=senior_app_user,
            prefix="account",
        )

        profile_form = AdminSeniorProfileForm(
            instance=senior_profile,
            prefix="profile",
        )

        emergency_form = AdminEmergencyContactForm(
            instance=emergency_contact,
            prefix="emergency",
        )
        
    return render(
        request,
        "adminPortal/edit_senior.html",
        {
            "app_user": app_user,
            "senior_profile": senior_profile,
            "senior_app_user": senior_app_user,

            "account_form": account_form,
            "profile_form": profile_form,
            "emergency_form": emergency_form,
        },
    )
        
# ==================================================
# ADMIN - ALL VOLUNTEERS
# ==================================================

@login_required(login_url="login")
def admin_volunteers(request):

    # ==================================================
    # ADMIN ACCESS
    # ==================================================

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


    # ==================================================
    # SEARCH
    # ==================================================

    search_query = request.GET.get(
        "search",
        "",
    ).strip()

    volunteers = (
        VolunteerProfile.objects
        .select_related(
            "app_user",
            "app_user__user",
        )
        .order_by(
            "app_user__full_name"
        )
    )

    if search_query:
        volunteers = volunteers.filter(
            app_user__full_name__icontains=search_query
        )


    # ==================================================
    # PREPARE VOLUNTEER DISPLAY DATA
    # ==================================================

    volunteer_rows = []

    for volunteer in volunteers:

        skills = []

        if volunteer.regular_check_ins:
            skills.append(
                {
                    "label": "Welfare Check",
                    "class": "skill-blue",
                }
            )

        if volunteer.mobility_assistance:
            skills.append(
                {
                    "label": "Mobility",
                    "class": "skill-purple",
                }
            )

        if volunteer.meal_assistance:
            skills.append(
                {
                    "label": "Meal Assistance",
                    "class": "skill-orange",
                }
            )

        if volunteer.emotional_support:
            skills.append(
                {
                    "label": "Emotional Support",
                    "class": "skill-red",
                }
            )

        if volunteer.medical_assistance:
            skills.append(
                {
                    "label": "Medical Support",
                    "class": "skill-green",
                }
            )

        if volunteer.other_support:
            skills.append(
                {
                    "label": volunteer.other_support,
                    "class": "skill-grey",
                }
            )

        volunteer_rows.append(
            {
                "profile": volunteer,

                "volunteer_id": (
                    f"VOL-{volunteer.pk:04d}"
                ),

                "status": (
                    "active"
                    if volunteer.app_user.user.is_active
                    else "inactive"
                ),

                # Only show the first 2 main skills
                "skills": skills[:2],
            }
        )


    # ==================================================
    # SUMMARY COUNTS
    # ==================================================

    total_volunteers = (
        VolunteerProfile.objects.count()
    )

    active_volunteers = (
        VolunteerProfile.objects
        .filter(
            app_user__user__is_active=True
        )
        .count()
    )

    inactive_volunteers = (
        VolunteerProfile.objects
        .filter(
            app_user__user__is_active=False
        )
        .count()
    )

    available_volunteers = (
        VolunteerAvailability.objects
        .filter(
            date__gte=date.today(),
            available=True,
        )
        .values("volunteer")
        .distinct()
        .count()
    )


    # ==================================================
    # RENDER PAGE
    # ==================================================

    context = {
        "app_user": app_user,

        "volunteer_rows": volunteer_rows,

        "total_volunteers": total_volunteers,
        "active_volunteers": active_volunteers,
        "inactive_volunteers": inactive_volunteers,
        "available_volunteers": available_volunteers,

        "search_query": search_query,
    }

    return render(
        request,
        "adminPortal/volunteers.html",
        context,
    )


    # ==================================================
    # SUMMARY COUNTS
    # ==================================================

    total_volunteers = (
        VolunteerProfile.objects.count()
    )

    active_volunteers = (
        VolunteerProfile.objects
        .filter(
            app_user__user__is_active=True
        )
        .count()
    )

    inactive_volunteers = (
        VolunteerProfile.objects
        .filter(
            app_user__user__is_active=False
        )
        .count()
    )

    available_volunteers = (
        VolunteerAvailability.objects
        .filter(
            date__gte=date.today(),
            available=True,
        )
        .values("volunteer")
        .distinct()
        .count()
    )


    # ==================================================
    # RENDER PAGE
    # ==================================================

    context = {
        "app_user": app_user,

        "volunteer_rows": volunteer_rows,

        "total_volunteers": total_volunteers,
        "active_volunteers": active_volunteers,
        "inactive_volunteers": inactive_volunteers,
        "available_volunteers": available_volunteers,

        "search_query": search_query,
    }

    return render(
        request,
        "adminPortal/volunteers.html",
        context,
    )

# ==================================================
# ADMIN - INDIVIDUAL VOLUNTEER
# ==================================================

@login_required(login_url="login")
def admin_volunteer_detail(request, volunteer_id):
    

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")

    volunteer_profile = get_object_or_404(
        VolunteerProfile.objects.select_related(
            "app_user",
            "app_user__user",
        ),
        pk=volunteer_id,
    )
    
    # Seniors currently assigned to this volunteer
    assigned_seniors = (
        SeniorVolunteerAssignment.objects
        .filter(
            volunteer=volunteer_profile,
            active=True,
        )
        .select_related(
            "senior",
            "senior__app_user",
        )
        .order_by(
            "senior__app_user__full_name"
        )
    )

    # All active seniors that can be selected
    all_seniors = (
        SeniorProfile.objects
        .select_related(
            "app_user",
            "app_user__user",
        )
        .filter(
            app_user__user__is_active=True,
        )
        .order_by(
            "app_user__full_name"
        )
    )

    birth_date = volunteer_profile.app_user.date_of_birth
    today = date.today()

    age = (
        today.year
        - birth_date.year
        - (
            (today.month, today.day)
            <
            (
                birth_date.month,
                birth_date.day,
            )
        )
    )

    return render(
        request,
        "adminPortal/volunteer_detail.html",
        {
            "app_user": app_user,
            "volunteer_profile": volunteer_profile,
            "volunteer_app_user": volunteer_profile.app_user,
            "age": age,

            "assigned_seniors": assigned_seniors,
            "all_seniors": all_seniors,
        },
    )

# ==================================================
# ADMIN - EDIT VOLUNTEER
# ==================================================

@login_required(login_url="login")
def admin_edit_volunteer(request, volunteer_id):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")

    # ==================================================
    # GET EXISTING VOLUNTEER FROM DATABASE
    # ==================================================

    volunteer_profile = get_object_or_404(
        VolunteerProfile.objects.select_related(
            "app_user",
            "app_user__user",
        ),
        pk=volunteer_id,
    )

    volunteer_app_user = volunteer_profile.app_user

    # ==================================================
    # SAVE CHANGES
    # ==================================================

    if request.method == "POST":

        account_form = AdminVolunteerAccountForm(
            request.POST,
            instance=volunteer_app_user,
            prefix="account",
        )

        profile_form = AdminVolunteerProfileForm(
            request.POST,
            instance=volunteer_profile,
            prefix="profile",
        )

        if (
            account_form.is_valid()
            and profile_form.is_valid()
        ):

            with transaction.atomic():

                # Updates the existing AppUser record.
                account_form.save()

                # Updates the existing VolunteerProfile record.
                profile_form.save()

            messages.success(
                request,
                "Volunteer information updated successfully.",
            )

            return redirect(
                "admin_volunteer_detail",
                volunteer_id=volunteer_profile.pk,
            )

    # ==================================================
    # LOAD EXISTING DATABASE VALUES
    # ==================================================

    else:

        account_form = AdminVolunteerAccountForm(
            instance=volunteer_app_user,
            prefix="account",
        )

        profile_form = AdminVolunteerProfileForm(
            instance=volunteer_profile,
            prefix="profile",
        )

    return render(
        request,
        "adminPortal/edit_volunteer.html",
        {
            "app_user": app_user,

            "volunteer_profile": volunteer_profile,
            "volunteer_app_user": volunteer_app_user,

            "account_form": account_form,
            "profile_form": profile_form,
        },
    )

# ==================================================
# ADMIN - ASSIGN SENIOR TO VOLUNTEER
# ==================================================

@login_required(login_url="login")
def admin_assign_senior_to_volunteer(request, volunteer_id):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to perform this action.",
        )
        return redirect("home")

    # Get volunteer from database
    volunteer_profile = get_object_or_404(
        VolunteerProfile,
        pk=volunteer_id,
    )

    if request.method == "POST":

        senior_id = request.POST.get("senior_id")

        if not senior_id:

            messages.error(
                request,
                "Please select a senior.",
            )

            return redirect(
                "admin_volunteer_detail",
                volunteer_id=volunteer_profile.pk,
            )

        senior_profile = get_object_or_404(
            SeniorProfile,
            pk=senior_id,
        )

        with transaction.atomic():

            # A senior should only have one active volunteer assignment at one time.
            SeniorVolunteerAssignment.objects.filter(
                senior=senior_profile,
                active=True,
            ).update(
                active=False
            )

            # Creates a new active assignment.
            SeniorVolunteerAssignment.objects.create(
                senior=senior_profile,
                volunteer=volunteer_profile,
                active=True,
            )

        messages.success(
            request,
            (
                f"{senior_profile.app_user.full_name} "
                f"has been assigned to "
                f"{volunteer_profile.app_user.full_name}."
            ),
        )

    return redirect(
        "admin_volunteer_detail",
        volunteer_id=volunteer_profile.pk,
    )

# ==================================================
# ADMIN - REMOVE SENIOR FROM VOLUNTEER
# ==================================================

@login_required(login_url="login")
def admin_remove_senior_from_volunteer(request, assignment_id):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to perform this action.",
        )
        return redirect("home")

    assignment = get_object_or_404(
        SeniorVolunteerAssignment.objects.select_related(
            "senior",
            "senior__app_user",
            "volunteer",
            "volunteer__app_user",
        ),
        pk=assignment_id,
        active=True,
    )

    volunteer_id = assignment.volunteer.pk

    if request.method == "POST":

        assignment.active = False
        assignment.save(update_fields=["active"])

        messages.success(
            request,
            (
                f"{assignment.senior.app_user.full_name} "
                f"has been removed from "
                f"{assignment.volunteer.app_user.full_name}."
            ),
        )

    return redirect(
        "admin_volunteer_detail",
        volunteer_id=volunteer_id,
    )

# ==================================================
# ADMIN - VISITS & SCHEDULE
# ==================================================

@login_required(login_url="login")
def admin_visits_schedule(request):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")


    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


    today = date.today()


    # ==================================================
    # SEARCH / FILTER
    # ==================================================

    search_query = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    visit_type_filter = request.GET.get(
        "visit_type",
        "",
    ).strip()


    # ==================================================
    # ALL VISITS
    # ==================================================

    visits = (
        ScheduledVisit.objects
        .select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
            "assignment__volunteer",
            "assignment__volunteer__app_user",
        )
        .order_by(
            "-visit_date",
            "-start_time",
        )
    )


    # ==================================================
    # SEARCH
    # ==================================================

    if search_query:

        from django.db.models import Q

        visits = visits.filter(
            Q(
                assignment__senior__app_user__full_name__icontains=
                search_query
            )
            |
            Q(
                assignment__volunteer__app_user__full_name__icontains=
                search_query
            )
        )


    # ==================================================
    # VISIT TYPE FILTER
    # ==================================================

    if visit_type_filter:

        visits = visits.filter(
            visit_type=visit_type_filter
        )


    # ==================================================
    # PREPARE DISPLAY DATA
    #
    # A scheduled visit whose date has passed is
    # displayed as "Missed".
    # ==================================================

    visit_rows = []

    for visit in visits:

        if (
            visit.status == "scheduled"
            and visit.visit_date < today
        ):
            display_status = "Missed"
            display_status_class = "missed"

        elif visit.status == "scheduled":
            display_status = "Upcoming"
            display_status_class = "scheduled"

        elif visit.status == "completed":
            display_status = "Completed"
            display_status_class = "completed"

        else:
            display_status = "Cancelled"
            display_status_class = "cancelled"


        visit_rows.append(
            {
                "visit": visit,
                "display_status": display_status,
                "display_status_class": display_status_class,
            }
        )


    # ==================================================
    # DISPLAY STATUS FILTER
    # ==================================================

    if status_filter:

        visit_rows = [
            row
            for row in visit_rows
            if row["display_status_class"] == status_filter
        ]


    # ==================================================
    # SUMMARY COUNTS
    # ==================================================

    total_visits = (
        ScheduledVisit.objects.count()
    )


    completed_visits = (
        ScheduledVisit.objects
        .filter(
            status="completed"
        )
        .count()
    )


    upcoming_count = (
        ScheduledVisit.objects
        .filter(
            status="scheduled",
            visit_date__gte=today,
        )
        .count()
    )


    cancelled_count = (
        ScheduledVisit.objects
        .filter(
            status="cancelled"
        )
        .count()
    )


    missed_count = (
        ScheduledVisit.objects
        .filter(
            status="scheduled",
            visit_date__lt=today,
        )
        .count()
    )


    cancelled_missed_count = (
        cancelled_count + missed_count
    )


    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "adminPortal/visits_schedule.html",
        {
            "app_user": app_user,

            "visit_rows": visit_rows,

            "total_visits": total_visits,
            "completed_visits": completed_visits,
            "upcoming_count": upcoming_count,

            "cancelled_missed_count":
                cancelled_missed_count,

            "search_query": search_query,
            "status_filter": status_filter,
            "visit_type_filter": visit_type_filter,
        },
    )

# ==================================================
# ADMIN - CREATE SCHEDULED VISIT
# ==================================================

@login_required(login_url="login")
def admin_schedule_visit(request):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")


    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")

    # ==================================================
    # ACTIVE SENIOR / VOLUNTEER ASSIGNMENTS
    # ==================================================

    assignments = (
        SeniorVolunteerAssignment.objects
        .filter(
            active=True,
        )
        .select_related(
            "senior",
            "senior__app_user",
            "volunteer",
            "volunteer__app_user",
        )
        .order_by(
            "senior__app_user__full_name",
        )
    )


    # ==================================================
    # VOLUNTEER AVAILABILITY
    # ==================================================

    availability_slots = (
        VolunteerAvailability.objects
        .filter(
            date__gte=date.today(),
            available=True,
        )
        .select_related(
            "volunteer",
            "volunteer__app_user",
        )
        .order_by(
            "date",
            "start_time",
        )
    )


    # ==================================================
    # CREATE VISIT
    # ==================================================

    if request.method == "POST":

        assignment_id = request.POST.get(
            "assignment_id"
        )

        availability_id = request.POST.get(
            "availability_id"
        )

        visit_type = request.POST.get(
            "visit_type"
        )

        visit_purpose = request.POST.get(
            "visit_purpose"
        )

        support_types = request.POST.getlist(
            "support_types"
        )

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


        # ==================================================
        # VALIDATION
        # ==================================================

        if not assignment_id:

            messages.error(
                request,
                "Please select a senior and volunteer.",
            )

            return redirect(
                "admin_schedule_visit"
            )


        if not availability_id:

            messages.error(
                request,
                "Please select an available date and time.",
            )

            return redirect(
                "admin_schedule_visit"
            )


        if not visit_type or not visit_purpose:

            messages.error(
                request,
                "Please complete the visit details.",
            )

            return redirect(
                "admin_schedule_visit"
            )


        assignment = get_object_or_404(
            SeniorVolunteerAssignment.objects.select_related(
                "senior",
                "senior__app_user",
                "volunteer",
                "volunteer__app_user",
            ),
            pk=assignment_id,
            active=True,
        )


        availability = get_object_or_404(
            VolunteerAvailability,
            pk=availability_id,
            volunteer=assignment.volunteer,
            available=True,
        )


        # ==================================================
        # CHECK THAT SLOT IS NOT ALREADY BOOKED
        # ==================================================

        slot_taken = (
            ScheduledVisit.objects
            .filter(
                assignment__volunteer=
                assignment.volunteer,

                visit_date=
                availability.date,

                start_time=
                availability.start_time,

                status="scheduled",
            )
            .exists()
        )


        if slot_taken:

            messages.error(
                request,
                "That volunteer time slot has already been scheduled.",
            )

            return redirect(
                "admin_schedule_visit"
            )


        # ==================================================
        # CALCULATE END TIME
        # ==================================================

        try:

            duration_minutes = int(
                estimated_duration
            )

        except (
            TypeError,
            ValueError,
        ):

            duration_minutes = 60


        start_datetime = datetime.combine(
            availability.date,
            availability.start_time,
        )


        end_datetime = (
            start_datetime
            + timedelta(
                minutes=duration_minutes
            )
        )


        # ==================================================
        # SAVE
        # ==================================================

        with transaction.atomic():

            ScheduledVisit.objects.create(

                assignment=assignment,

                visit_type=visit_type,

                visit_purpose=visit_purpose,

                support_types=support_types,

                other_support_details=
                other_support_details,

                visit_date=
                availability.date,

                start_time=
                availability.start_time,

                end_time=
                end_datetime.time(),

                estimated_duration=
                duration_minutes,

                notes=notes,

                status="scheduled",
            )


        messages.success(
            request,
            (
                f"Visit scheduled for "
                f"{assignment.senior.app_user.full_name} "
                f"with "
                f"{assignment.volunteer.app_user.full_name}."
            ),
        )


        return redirect(
            "admin_visits_schedule"
        )


    return render(
        request,
        "adminPortal/schedule_visit.html",
        {
            "app_user": app_user,
            "assignments": assignments,
            "availability_slots": availability_slots,

            "visit_type_choices":
            ScheduledVisit.VISIT_TYPE_CHOICES,

            "visit_purpose_choices":
            ScheduledVisit.VISIT_PURPOSE_CHOICES,
        },
    )

# ==================================================
# ADMIN VISIT DETAILS / VIEW BUTTON
# ==================================================

@login_required(login_url="login")
def admin_visit_detail(request, visit_id):

    try:
        app_user = AppUser.objects.get(user=request.user)
    except AppUser.DoesNotExist:
        return redirect("login")

    if app_user.account_type != "admin":
        return redirect("login")

    visit = get_object_or_404(
        ScheduledVisit.objects.select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
            "assignment__volunteer",
            "assignment__volunteer__app_user",
        ),
        pk=visit_id,
    )

    return render(
        request,
        "adminPortal/visit_details.html",
        {
            "app_user": app_user,
            "visit": visit,
        },
    )


# ==================================================
# ADMIN VISIT DETAILS / EDIT BUTTON
# ==================================================

@login_required(login_url="login")
def admin_edit_visit(request, visit_id):

    try:
        app_user = AppUser.objects.get(user=request.user)
    except AppUser.DoesNotExist:
        return redirect("login")

    if app_user.account_type != "admin":
        return redirect("login")

    visit = get_object_or_404(
        ScheduledVisit.objects.select_related(
            "assignment",
            "assignment__senior",
            "assignment__senior__app_user",
            "assignment__volunteer",
            "assignment__volunteer__app_user",
        ),
        pk=visit_id,
    )

    assignments = (
        SeniorVolunteerAssignment.objects
        .filter(active=True)
        .select_related(
            "senior",
            "senior__app_user",
            "volunteer",
            "volunteer__app_user",
        )
        .order_by("senior__app_user__full_name")
    )

    availability_slots = (
        VolunteerAvailability.objects
        .filter(
            available=True,
            date__gte=date.today(),
        )
        .select_related(
            "volunteer",
            "volunteer__app_user",
        )
        .order_by(
            "date",
            "start_time",
        )
    )

    if request.method == "POST":

        assignment_id = request.POST.get("assignment_id")
        availability_id = request.POST.get("availability_id")

        visit_type = request.POST.get("visit_type")
        visit_purpose = request.POST.get("visit_purpose")

        support_types = request.POST.getlist("support_types")

        other_support_details = request.POST.get(
            "other_support_details",
            "",
        ).strip()

        estimated_duration = request.POST.get(
            "estimated_duration",
            "60",
        )

        notes = request.POST.get(
            "notes",
            "",
        ).strip()

        status = request.POST.get(
            "status",
            "scheduled",
        )

        if not assignment_id:
            messages.error(
                request,
                "Please select a senior and volunteer.",
            )
            return redirect(
                "admin_edit_visit",
                visit_id=visit.pk,
            )

        if not visit_type or not visit_purpose:
            messages.error(
                request,
                "Please complete the visit details.",
            )
            return redirect(
                "admin_edit_visit",
                visit_id=visit.pk,
            )

        assignment = get_object_or_404(
            SeniorVolunteerAssignment.objects.select_related(
                "senior",
                "senior__app_user",
                "volunteer",
                "volunteer__app_user",
            ),
            pk=assignment_id,
            active=True,
        )

        try:
            duration_minutes = int(estimated_duration)
        except (TypeError, ValueError):
            duration_minutes = visit.estimated_duration or 60

        new_visit_date = visit.visit_date
        new_start_time = visit.start_time

        current_start_datetime = datetime.combine(
            visit.visit_date,
            visit.start_time,
        )

        current_end_datetime = (
            current_start_datetime
            + timedelta(minutes=duration_minutes)
        )

        new_end_time = current_end_datetime.time()

        if availability_id:

            availability = get_object_or_404(
                VolunteerAvailability.objects.select_related(
                    "volunteer",
                    "volunteer__app_user",
                ),
                pk=availability_id,
                available=True,
            )

            if availability.volunteer_id != assignment.volunteer_id:
                messages.error(
                    request,
                    "The selected availability does not belong to the assigned volunteer.",
                )
                return redirect(
                    "admin_edit_visit",
                    visit_id=visit.pk,
                )

            start_datetime = datetime.combine(
                availability.date,
                availability.start_time,
            )

            end_datetime = (
                start_datetime
                + timedelta(minutes=duration_minutes)
            )

            availability_end_datetime = datetime.combine(
                availability.date,
                availability.end_time,
            )

            if end_datetime > availability_end_datetime:
                messages.error(
                    request,
                    "The visit duration exceeds the volunteer's available time.",
                )
                return redirect(
                    "admin_edit_visit",
                    visit_id=visit.pk,
                )

            conflicting_visit = (
                ScheduledVisit.objects
                .filter(
                    assignment__volunteer=assignment.volunteer,
                    visit_date=availability.date,
                    status="scheduled",
                )
                .exclude(pk=visit.pk)
                .filter(
                    start_time__lt=end_datetime.time(),
                    end_time__gt=availability.start_time,
                )
                .exists()
            )

            if conflicting_visit:
                messages.error(
                    request,
                    "This volunteer already has another visit during the selected time.",
                )
                return redirect(
                    "admin_edit_visit",
                    visit_id=visit.pk,
                )

            new_visit_date = availability.date
            new_start_time = availability.start_time
            new_end_time = end_datetime.time()

        with transaction.atomic():

            visit.assignment = assignment
            visit.visit_type = visit_type
            visit.visit_purpose = visit_purpose
            visit.support_types = support_types
            visit.other_support_details = other_support_details
            visit.visit_date = new_visit_date
            visit.start_time = new_start_time
            visit.end_time = new_end_time
            visit.estimated_duration = duration_minutes
            visit.notes = notes
            visit.status = status

            visit.save()

        messages.success(
            request,
            "Visit updated successfully.",
        )

        return redirect(
            "admin_visit_detail",
            visit_id=visit.pk,
        )

    return render(
        request,
        "adminPortal/edit_visit.html",
        {
            "app_user": app_user,
            "visit": visit,
            "assignments": assignments,
            "availability_slots": availability_slots,
            "visit_type_choices": ScheduledVisit.VISIT_TYPE_CHOICES,
            "visit_purpose_choices": ScheduledVisit.VISIT_PURPOSE_CHOICES,
            "status_choices": ScheduledVisit.STATUS_CHOICES,
        },
    )

# ==================================================
# ADMIN REPORTS
# ==================================================

@login_required(login_url="login")
def admin_reports(request):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")


    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


    reports = (
        VisitReport.objects
        .select_related(
            "visit",
            "visit__assignment",
            "visit__assignment__senior",
            "visit__assignment__senior__app_user",
            "visit__assignment__volunteer",
            "visit__assignment__volunteer__app_user",
        )
        .order_by(
            "-submitted_at"
        )
    )


    total_reports = reports.count()

    follow_up_count = (
        reports
        .filter(
            follow_up_required=True
        )
        .count()
    )

    concern_count = (
        reports
        .exclude(
            concerns=""
        )
        .count()
    )


    return render(
        request,
        "adminPortal/reports.html",
        {
            "app_user": app_user,
            "reports": reports,

            "total_reports": total_reports,
            "follow_up_count": follow_up_count,
            "concern_count": concern_count,
        },
    )

# ==================================================
# ADMIN - VIEW REPORT
# ==================================================

@login_required(login_url="login")
def admin_view_report(request, report_id):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")


    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


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
    )


    return render(
        request,
        "adminPortal/report_detail.html",
        {
            "app_user": app_user,
            "report": report,
            "visit": report.visit,
        },
    )

# ==================================================
# ADMIN - SUPPORT REQUESTS
# ==================================================

@login_required(login_url="login")
def admin_support_requests(request):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")


    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


    status_filter = request.GET.get(
        "status",
        "",
    ).strip()


    support_requests = (
        SupportRequest.objects
        .select_related(
            "senior",
            "senior__app_user",
        )
        .order_by(
            "-submitted_at"
        )
    )


    if status_filter:
        support_requests = support_requests.filter(
            status=status_filter
        )


    total_requests = SupportRequest.objects.count()

    pending_requests = (
        SupportRequest.objects
        .filter(
            status="pending"
        )
        .count()
    )

    reviewing_requests = (
        SupportRequest.objects
        .filter(
            status="reviewing"
        )
        .count()
    )

    active_requests = (
        SupportRequest.objects
        .filter(
            status__in=[
                "approved",
                "ongoing",
            ]
        )
        .count()
    )


    return render(
        request,
        "adminPortal/support_requests.html",
        {
            "app_user": app_user,

            "support_requests": support_requests,

            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "reviewing_requests": reviewing_requests,
            "active_requests": active_requests,

            "status_filter": status_filter,
            "status_choices": SupportRequest.STATUS_CHOICES,
        },
    )

# ==================================================
# ADMIN - SUPPORT REQUEST DETAIL
# ==================================================

@login_required(login_url="login")
def admin_support_request_detail(request, request_id):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")


    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


    support_request = get_object_or_404(
        SupportRequest.objects.select_related(
            "senior",
            "senior__app_user",
        ),
        pk=request_id,
    )


    if request.method == "POST":

        new_status = request.POST.get(
            "status",
            support_request.status,
        )

        admin_notes = request.POST.get(
            "admin_notes",
            "",
        ).strip()


        valid_statuses = dict(
            SupportRequest.STATUS_CHOICES
        )


        if new_status not in valid_statuses:

            messages.error(
                request,
                "Invalid support request status.",
            )

            return redirect(
                "admin_support_request_detail",
                request_id=support_request.pk,
            )


        support_request.status = new_status
        support_request.admin_notes = admin_notes

        support_request.save(
            update_fields=[
                "status",
                "admin_notes",
                "updated_at",
            ]
        )


        messages.success(
            request,
            "Support request updated successfully.",
        )


        return redirect(
            "admin_support_request_detail",
            request_id=support_request.pk,
        )


    return render(
        request,
        "adminPortal/support_request_detail.html",
        {
            "app_user": app_user,
            "support_request": support_request,
            "status_choices": SupportRequest.STATUS_CHOICES,
        },
    )

# ==================================================
# ADMIN - ALERTS
# ==================================================

@login_required(login_url="login")
def admin_alerts(request):

    # ==================================================
    # GET LOGGED-IN USER
    # ==================================================

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )

        return redirect("home")


    # ==================================================
    # ADMIN-ONLY ACCESS
    # ==================================================

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )

        return redirect("home")


    # ==================================================
    # GET WELLBEING ALERTS
    # ==================================================

    wellbeing_submissions = (
        WellbeingSubmission.objects
        .filter(
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
        .order_by(
            "-submitted_at"
        )
    )


    # ==================================================
    # PREPARE ALERT DISPLAY DATA
    # ==================================================

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
                    submission
                    .senior
                    .app_user
                    .full_name
                ),

                "feeling": (
                    submission
                    .get_feeling_display()
                ),

                "notes": submission.notes,

                "submitted_at": (
                    submission.submitted_at
                ),

                "priority": priority,

                "priority_label": priority_label,
            }
        )


    # ==================================================
    # SUMMARY COUNTS
    # ==================================================

    total_alerts = len(alerts)

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


    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "adminPortal/alerts.html",
        {
            "app_user": app_user,

            "alerts": alerts,

            "total_alerts": total_alerts,
            "high_priority_count": high_priority_count,
            "medium_priority_count": medium_priority_count,
        },
    )

# ==================================================
# ADMIN - ALERT DETAIL
# ==================================================

@login_required(login_url="login")
def admin_alert_detail(request, submission_id):

    # ==================================================
    # GET LOGGED-IN USER
    # ==================================================

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:

        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )

        return redirect("home")


    # ==================================================
    # ADMIN-ONLY ACCESS
    # ==================================================

    if app_user.account_type != "admin":

        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )

        return redirect("home")


    # ==================================================
    # GET WELLBEING SUBMISSION
    # ==================================================

    submission = get_object_or_404(
        WellbeingSubmission.objects.select_related(
            "senior",
            "senior__app_user",
        ),
        pk=submission_id,
    )


    # ==================================================
    # MARK ALERT AS RESOLVED
    # ==================================================

    if request.method == "POST":

        if not submission.is_resolved:

            from django.utils import timezone

            submission.is_resolved = True
            submission.resolved_at = timezone.now()

            submission.save(
                update_fields=[
                    "is_resolved",
                    "resolved_at",
                ]
            )

            messages.success(
                request,
                (
                    f"The wellbeing alert for "
                    f"{submission.senior.app_user.full_name} "
                    f"has been marked as resolved."
                ),
            )

        return redirect(
            "admin_alerts"
        )


    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "adminPortal/alert_detail.html",
        {
            "app_user": app_user,
            "submission": submission,
            "senior": submission.senior,
        },
    )

# ==================================================
# ADMIN - ADD VOLUNTEER
# ==================================================

@login_required(login_url="login")
def admin_add_volunteer(request):

    # ==================================================
    # ADMIN ACCESS
    # ==================================================

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")

    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


    # ==================================================
    # FORM
    # ==================================================

    if request.method == "POST":
        form = AdminAddVolunteerForm(
            request.POST
        )

        if form.is_valid():

            email = (
                form.cleaned_data["email"]
                .strip()
                .lower()
            )

            nric_fin = (
                form.cleaned_data["nric_fin"]
                .strip()
                .upper()
            )

            try:

                # ==================================================
                # CREATE ALL DATABASE RECORDS TOGETHER
                # ==================================================

                with transaction.atomic():

                    # ----------------------------------------------
                    # DJANGO USER
                    # ----------------------------------------------

                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=form.cleaned_data[
                            "password"
                        ],
                    )

                    # ----------------------------------------------
                    # APP USER
                    # ----------------------------------------------

                    new_app_user = AppUser.objects.create(
                        user=user,
                        account_type="volunteer",

                        full_name=(
                            form.cleaned_data[
                                "full_name"
                            ].strip()
                        ),

                        nric_fin=nric_fin,

                        mobile_number=(
                            form.cleaned_data[
                                "mobile_number"
                            ].strip()
                        ),

                        date_of_birth=(
                            form.cleaned_data[
                                "date_of_birth"
                            ]
                        ),
                    )

                    # ----------------------------------------------
                    # VOLUNTEER PROFILE
                    # ----------------------------------------------

                    VolunteerProfile.objects.create(
                        app_user=new_app_user,

                        address=(
                            form.cleaned_data[
                                "address"
                            ].strip()
                        ),

                        postal_code=(
                            form.cleaned_data[
                                "postal_code"
                            ].strip()
                        ),

                        unit_number=(
                            form.cleaned_data
                            .get(
                                "unit_number",
                                "",
                            )
                            .strip()
                        ),

                        preferred_language=(
                            form.cleaned_data[
                                "preferred_language"
                            ]
                        ),

                        regular_check_ins=(
                            form.cleaned_data.get(
                                "regular_check_ins",
                                False,
                            )
                        ),

                        mobility_assistance=(
                            form.cleaned_data.get(
                                "mobility_assistance",
                                False,
                            )
                        ),

                        meal_assistance=(
                            form.cleaned_data.get(
                                "meal_assistance",
                                False,
                            )
                        ),

                        emotional_support=(
                            form.cleaned_data.get(
                                "emotional_support",
                                False,
                            )
                        ),

                        medical_assistance=(
                            form.cleaned_data.get(
                                "medical_assistance",
                                False,
                            )
                        ),

                        other_support=(
                            form.cleaned_data
                            .get(
                                "other_support",
                                "",
                            )
                            .strip()
                        ),

                        transport_available=(
                            form.cleaned_data[
                                "transport_available"
                            ]
                            == "yes"
                        ),

                        additional_notes=(
                            form.cleaned_data
                            .get(
                                "additional_notes",
                                "",
                            )
                            .strip()
                        ),
                    )


                # ==================================================
                # SUCCESS
                # ==================================================

                messages.success(
                    request,
                    (
                        "Volunteer account created successfully. "
                        "The volunteer can now log in using "
                        "their email address and password."
                    ),
                )

                return redirect(
                    "admin_volunteers"
                )


            except Exception as error:
                print("ADD VOLUNTEER ERROR:", error)

                messages.error(
                    request,
                    f"Volunteer account could not be created: {error}",
                )

    else:
        form = AdminAddVolunteerForm()


    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "adminPortal/add_volunteer.html",
        {
            "app_user": app_user,
            "form": form,
        },
    )

# ==================================================
# ADMIN - MY PROFILE
# ==================================================

@login_required(login_url="login")
def admin_profile(request):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")


    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


    birth_date = app_user.date_of_birth
    today = date.today()

    age = (
        today.year
        - birth_date.year
        - (
            (today.month, today.day)
            < (birth_date.month, birth_date.day)
        )
    )


    return render(
        request,
        "adminPortal/profile.html",
        {
            "app_user": app_user,
            "age": age,
        },
    )

# ==================================================
# ADMIN - EDIT MY PROFILE
# ==================================================

@login_required(login_url="login")
def admin_edit_profile(request):

    try:
        app_user = request.user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            "Your CircleCareSG account profile could not be found.",
        )
        return redirect("home")


    if app_user.account_type != "admin":
        messages.error(
            request,
            "You do not have permission to access the Admin Portal.",
        )
        return redirect("home")


    if request.method == "POST":

        form = AdminProfileForm(
            request.POST,
            request.FILES,
            instance=app_user,
        )

        if form.is_valid():

            try:

                with transaction.atomic():
                    form.save()

                messages.success(
                    request,
                    "Your profile has been updated successfully.",
                )

                return redirect(
                    "admin_profile"
                )

            except Exception:

                messages.error(
                    request,
                    (
                        "Your profile could not be updated. "
                        "Please try again."
                    ),
                )

    else:

        form = AdminProfileForm(
            instance=app_user
        )


    return render(
        request,
        "adminPortal/edit_profile.html",
        {
            "app_user": app_user,
            "form": form,
        },
    )
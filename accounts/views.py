from datetime import date

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from .forms import (
    LoginForm,
    RegistrationStepOneForm,
    SeniorRegistrationStepTwoForm,
    VolunteerRegistrationStepTwoForm,
)
from .models import (
    AppUser,
    EmergencyContact,
    SeniorProfile,
    VolunteerProfile,
)


# Authentication

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data[
                "email"
            ].strip().lower()

            password = form.cleaned_data[
                "password"
            ]

            remember_me = form.cleaned_data.get(
                "remember_me",
                False,
            )

            user = authenticate(
                request,
                username=email,
                password=password,
            )

            if user is not None:
                auth_login(request, user)

                if remember_me:
                    request.session.set_expiry(
                        60 * 60 * 24 * 14
                    )
                else:
                    request.session.set_expiry(0)

                messages.success(
                    request,
                    (
                        "Welcome back, "
                        f"{get_user_display_name(user)}!"
                    ),
                )

                return redirect_user_by_role(
                    request
                )

            form.add_error(
                None,
                "The email address or password is incorrect.",
            )

    else:
        form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


def redirect_user_by_role(request):
    user = request.user

    if not user.is_authenticated:
        return redirect("login")

    if user.is_superuser:
        return redirect("home")

    try:
        app_user = user.app_profile

    except AppUser.DoesNotExist:
        messages.error(
            request,
            (
                "This user does not have a "
                "CircleCareSG profile."
            ),
        )

        auth_logout(request)

        return redirect("login")

    if app_user.account_type == "senior":
        return redirect("senior_dashboard")

    elif app_user.account_type == "guardian":
        return redirect("guardian_dashboard")

    elif app_user.account_type == "volunteer":
        return redirect("volunteer_dashboard")

    elif app_user.account_type == "admin":
        return redirect("admin_dashboard")

    messages.error(
        request,
        "Your account type could not be recognised.",
    )

    return redirect("home")


def get_user_display_name(user):
    try:
        return user.app_profile.full_name

    except AppUser.DoesNotExist:
        return user.username


def logout_view(request):
    auth_logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("login")


# Registration - Step 1

def register_step_one(request):
    initial_data = request.session.get(
        "registration_step_one",
        {},
    )

    if request.method == "POST":
        form = RegistrationStepOneForm(
            request.POST
        )

        if form.is_valid():
            request.session[
                "registration_step_one"
            ] = {
                "account_type": (
                    form.cleaned_data[
                        "account_type"
                    ]
                ),
                "full_name": (
                    form.cleaned_data[
                        "full_name"
                    ]
                ),
                "nric_fin": (
                    form.cleaned_data[
                        "nric_fin"
                    ]
                ),
                "mobile_number": (
                    form.cleaned_data[
                        "mobile_number"
                    ]
                ),
                "email": (
                    form.cleaned_data[
                        "email"
                    ]
                ),
                "date_of_birth": (
                    form.cleaned_data[
                        "date_of_birth"
                    ].isoformat()
                ),
                "password": (
                    form.cleaned_data[
                        "password"
                    ]
                ),
            }

            # Clear Step 2 data if the user
            # changes account type
            request.session.pop(
                "registration_step_two",
                None,
            )

            request.session.modified = True

            return redirect(
                "register_step_two"
            )

    else:
        form = RegistrationStepOneForm(
            initial=initial_data
        )

    return render(
        request,
        "accounts/register_step_one.html",
        {
            "form": form,
            "current_step": 1,
        },
    )


# Registration - Step 2

def register_step_two(request):
    step_one_data = request.session.get(
        "registration_step_one"
    )

    if not step_one_data:
        return redirect("register")

    account_type = step_one_data.get(
        "account_type"
    )

    initial_data = request.session.get(
        "registration_step_two",
        {},
    )

    if account_type == "senior":
        form_class = (
            SeniorRegistrationStepTwoForm
        )

        template_name = (
            "accounts/register_step_two.html"
        )

    elif account_type == "volunteer":
        form_class = (
            VolunteerRegistrationStepTwoForm
        )

        template_name = (
            "accounts/"
            "register_volunteer_step_two.html"
        )

    else:
        messages.error(
            request,
            (
                "This account type is not "
                "available for public registration."
            ),
        )

        # Remove invalid registration data
        request.session.pop(
            "registration_step_one",
            None,
        )

        request.session.pop(
            "registration_step_two",
            None,
        )

        request.session.modified = True

        return redirect("register")

    if request.method == "POST":
        form = form_class(request.POST)

        if form.is_valid():
            cleaned_data = (
                form.cleaned_data.copy()
            )

            # Convert volunteer transport
            # choice to a boolean
            if account_type == "volunteer":
                cleaned_data[
                    "transport_available"
                ] = (
                    cleaned_data.get(
                        "transport_available"
                    ) == "yes"
                )

            request.session[
                "registration_step_two"
            ] = cleaned_data

            request.session.modified = True

            return redirect(
                "register_review"
            )

    else:
        form = form_class(
            initial=initial_data
        )

    return render(
        request,
        template_name,
        {
            "form": form,
            "account_type": account_type,
            "current_step": 2,
        },
    )


# Registration - Review and submit

def register_review(request):
    step_one_data = request.session.get(
        "registration_step_one"
    )

    step_two_data = request.session.get(
        "registration_step_two"
    )

    # Prevent users from skipping
    # registration steps
    if not step_one_data:
        return redirect("register")

    if not step_two_data:
        return redirect(
            "register_step_two"
        )

    account_type = step_one_data.get(
        "account_type"
    )

    # Only Senior and Volunteer accounts
    # can be created through public registration
    if account_type not in [
        "senior",
        "volunteer",
    ]:
        messages.error(
            request,
            (
                "This account type is not "
                "available for public registration."
            ),
        )

        request.session.pop(
            "registration_step_one",
            None,
        )

        request.session.pop(
            "registration_step_two",
            None,
        )

        request.session.modified = True

        return redirect("register")

    # Prepare support interests
    support_interest_labels = []

    support_interest_map = [
        (
            "regular_check_ins",
            "Regular Check-ins",
        ),
        (
            "mobility_assistance",
            "Mobility Assistance",
        ),
        (
            "meal_assistance",
            "Meal Assistance",
        ),
        (
            "emotional_support",
            "Emotional Support",
        ),
        (
            "medical_assistance",
            "Medical Assistance",
        ),
    ]

    for field_name, label in (
        support_interest_map
    ):
        if step_two_data.get(field_name):
            support_interest_labels.append(
                label
            )

    if step_two_data.get("other_support"):
        support_interest_labels.append(
            step_two_data["other_support"]
        )

    if request.method == "POST":
        email = (
            step_one_data.get(
                "email",
                "",
            )
            .strip()
            .lower()
        )

        nric_fin = (
            step_one_data.get(
                "nric_fin",
                "",
            )
            .strip()
            .upper()
        )

        # Recheck unique details before
        # creating the account
        if User.objects.filter(
            username__iexact=email
        ).exists():
            messages.error(
                request,
                (
                    "An account with this email "
                    "address already exists."
                ),
            )

            return redirect("register")

        if User.objects.filter(
            email__iexact=email
        ).exists():
            messages.error(
                request,
                (
                    "An account with this email "
                    "address already exists."
                ),
            )

            return redirect("register")

        if AppUser.objects.filter(
            nric_fin__iexact=nric_fin
        ).exists():
            messages.error(
                request,
                (
                    "An account with this NRIC "
                    "or FIN already exists."
                ),
            )

            return redirect("register")

        # Convert the date stored in the
        # session back to a date object
        date_of_birth = (
            step_one_data.get(
                "date_of_birth"
            )
        )

        if isinstance(
            date_of_birth,
            str,
        ):
            try:
                date_of_birth = (
                    date.fromisoformat(
                        date_of_birth
                    )
                )

            except ValueError:
                messages.error(
                    request,
                    (
                        "The date of birth is "
                        "invalid. Please enter "
                        "it again."
                    ),
                )

                return redirect("register")

        try:
            # Create all records together
            # to avoid incomplete accounts
            with transaction.atomic():

                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=(
                        step_one_data[
                            "password"
                        ]
                    ),
                )

                app_user = (
                    AppUser.objects.create(
                        user=user,
                        account_type=(
                            account_type
                        ),
                        full_name=(
                            step_one_data[
                                "full_name"
                            ].strip()
                        ),
                        nric_fin=nric_fin,
                        mobile_number=(
                            step_one_data[
                                "mobile_number"
                            ].strip()
                        ),
                        date_of_birth=(
                            date_of_birth
                        ),
                    )
                )

                # Create Senior profile
                if account_type == "senior":

                    senior_profile = (
                        SeniorProfile.objects.create(
                            app_user=app_user,
                            address=(
                                step_two_data[
                                    "address"
                                ].strip()
                            ),
                            postal_code=(
                                step_two_data[
                                    "postal_code"
                                ].strip()
                            ),
                            unit_number=(
                                step_two_data.get(
                                    "unit_number",
                                    "",
                                ).strip()
                            ),
                            preferred_language=(
                                step_two_data[
                                    "preferred_language"
                                ]
                            ),
                            regular_check_ins=(
                                step_two_data.get(
                                    "regular_check_ins",
                                    False,
                                )
                            ),
                            mobility_assistance=(
                                step_two_data.get(
                                    "mobility_assistance",
                                    False,
                                )
                            ),
                            meal_assistance=(
                                step_two_data.get(
                                    "meal_assistance",
                                    False,
                                )
                            ),
                            emotional_support=(
                                step_two_data.get(
                                    "emotional_support",
                                    False,
                                )
                            ),
                            medical_assistance=(
                                step_two_data.get(
                                    "medical_assistance",
                                    False,
                                )
                            ),
                            other_support=(
                                step_two_data.get(
                                    "other_support",
                                    "",
                                ).strip()
                            ),
                        )
                    )

                    EmergencyContact.objects.create(
                        senior=senior_profile,
                        full_name=(
                            step_two_data[
                                "emergency_contact_name"
                            ].strip()
                        ),
                        relationship=(
                            step_two_data[
                                "emergency_contact_relationship"
                            ].strip()
                        ),
                        mobile_number=(
                            step_two_data[
                                "emergency_contact_mobile"
                            ].strip()
                        ),
                    )

                # Create Volunteer profile
                elif account_type == "volunteer":

                    VolunteerProfile.objects.create(
                        app_user=app_user,
                        address=(
                            step_two_data[
                                "address"
                            ].strip()
                        ),
                        postal_code=(
                            step_two_data[
                                "postal_code"
                            ].strip()
                        ),
                        unit_number=(
                            step_two_data.get(
                                "unit_number",
                                "",
                            ).strip()
                        ),
                        preferred_language=(
                            step_two_data[
                                "preferred_language"
                            ]
                        ),
                        regular_check_ins=(
                            step_two_data.get(
                                "regular_check_ins",
                                False,
                            )
                        ),
                        mobility_assistance=(
                            step_two_data.get(
                                "mobility_assistance",
                                False,
                            )
                        ),
                        meal_assistance=(
                            step_two_data.get(
                                "meal_assistance",
                                False,
                            )
                        ),
                        emotional_support=(
                            step_two_data.get(
                                "emotional_support",
                                False,
                            )
                        ),
                        medical_assistance=(
                            step_two_data.get(
                                "medical_assistance",
                                False,
                            )
                        ),
                        other_support=(
                            step_two_data.get(
                                "other_support",
                                "",
                            ).strip()
                        ),
                        transport_available=(
                            step_two_data.get(
                                "transport_available",
                                False,
                            )
                        ),
                        additional_notes=(
                            step_two_data.get(
                                "additional_notes",
                                "",
                            ).strip()
                        ),
                    )

        except KeyError:
            messages.error(
                request,
                (
                    "Some registration information "
                    "is missing. Please complete "
                    "the form again."
                ),
            )

            return redirect("register")

        except IntegrityError:
            messages.error(
                request,
                (
                    "The account could not be "
                    "created because the email "
                    "or NRIC/FIN is already "
                    "registered."
                ),
            )

            return redirect("register")

        # Remove temporary registration data
        # after successful registration
        request.session.pop(
            "registration_step_one",
            None,
        )

        request.session.pop(
            "registration_step_two",
            None,
        )

        request.session.modified = True

        messages.success(
            request,
            (
                "Your CircleCareSG account has "
                "been created successfully. "
                "You may now log in."
            ),
        )

        return redirect("login")

    return render(
        request,
        "accounts/register_review.html",
        {
            "step_one": step_one_data,
            "step_two": step_two_data,
            "account_type": account_type,
            "support_interest_labels": (
                support_interest_labels
            ),
            "current_step": 3,
        },
    )
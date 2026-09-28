from django import forms
from django.contrib.auth.models import User

from .models import (
    AppUser,
    SeniorProfile,
    VolunteerProfile,
)


class RegistrationStepOneForm(forms.Form):

    # Only seniors and volunteers can register publicly
    account_type = forms.ChoiceField(
        choices=[
            ("senior", "Senior"),
            ("volunteer", "Volunteer"),
        ],
        label="You are registering as",
    )

    # Basic account details
    full_name = forms.CharField(
        max_length=150,
        label="Your Name",
    )

    nric_fin = forms.CharField(
        max_length=20,
        label="NRIC / FIN",
    )

    mobile_number = forms.CharField(
        max_length=20,
        label="Mobile Number",
        initial="+65",
    )

    email = forms.EmailField(
        label="Email Address",
    )

    date_of_birth = forms.DateField(
        label="Date of Birth",
        widget=forms.DateInput(
            attrs={"type": "date"}
        ),
    )

    # Password fields
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        min_length=8,
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
    )

    # Check that the email is not already registered
    def clean_email(self):
        email = self.cleaned_data["email"].lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    # Check that the NRIC or FIN is not already registered
    def clean_nric_fin(self):
        nric_fin = self.cleaned_data["nric_fin"].upper()

        if AppUser.objects.filter(
            nric_fin__iexact=nric_fin
        ).exists():
            raise forms.ValidationError(
                "An account with this NRIC or FIN already exists."
            )

        return nric_fin

    # Make sure both passwords match
    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get(
            "confirm_password"
        )

        if (
            password
            and confirm_password
            and password != confirm_password
        ):
            self.add_error(
                "confirm_password",
                "The passwords do not match.",
            )

        return cleaned_data


class SeniorRegistrationStepTwoForm(forms.Form):

    # Personal and address details
    address = forms.CharField(
        max_length=255,
        label="Address",
    )

    postal_code = forms.CharField(
        max_length=10,
        label="Postal Code",
    )

    unit_number = forms.CharField(
        max_length=20,
        label="Unit / Floor",
        required=False,
    )

    preferred_language = forms.ChoiceField(
        choices=SeniorProfile.LANGUAGE_CHOICES,
        label="Preferred Language",
    )

    # Types of support the senior may need
    regular_check_ins = forms.BooleanField(
        required=False,
        label="Regular Check-ins",
    )

    mobility_assistance = forms.BooleanField(
        required=False,
        label="Mobility Assistance",
    )

    meal_assistance = forms.BooleanField(
        required=False,
        label="Meal Assistance",
    )

    emotional_support = forms.BooleanField(
        required=False,
        label="Emotional Support",
    )

    medical_assistance = forms.BooleanField(
        required=False,
        label="Medical Assistance",
    )

    other_support = forms.CharField(
        max_length=150,
        required=False,
        label="Other Support",
    )

    # Emergency contact details
    emergency_contact_name = forms.CharField(
        max_length=150,
        label="Emergency Contact Full Name",
    )

    emergency_contact_relationship = forms.CharField(
        max_length=50,
        label="Relationship",
    )

    emergency_contact_mobile = forms.CharField(
        max_length=20,
        label="Emergency Contact Mobile Number",
        initial="+65",
    )


class VolunteerRegistrationStepTwoForm(forms.Form):

    # Personal and address details
    address = forms.CharField(
        max_length=255,
        label="Address",
    )

    postal_code = forms.CharField(
        max_length=10,
        label="Postal Code",
    )

    unit_number = forms.CharField(
        max_length=20,
        label="Unit / Floor",
        required=False,
    )

    preferred_language = forms.ChoiceField(
        choices=VolunteerProfile.LANGUAGE_CHOICES,
        label="Preferred Language",
    )

    # Types of support the volunteer can provide
    regular_check_ins = forms.BooleanField(
        required=False,
        label="Regular Check-ins",
    )

    mobility_assistance = forms.BooleanField(
        required=False,
        label="Mobility Assistance",
    )

    meal_assistance = forms.BooleanField(
        required=False,
        label="Meal Assistance",
    )

    emotional_support = forms.BooleanField(
        required=False,
        label="Emotional Support",
    )

    medical_assistance = forms.BooleanField(
        required=False,
        label="Medical Assistance",
    )

    other_support = forms.CharField(
        max_length=150,
        required=False,
        label="Other Support",
    )

    # Volunteer availability and additional information
    transport_available = forms.ChoiceField(
        choices=[
            ("yes", "Yes"),
            ("no", "No"),
        ],
        widget=forms.RadioSelect,
        label="Transport Availability",
    )

    additional_notes = forms.CharField(
        required=False,
        label="Additional Notes",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Please specify",
            }
        ),
    )


class LoginForm(forms.Form):

    # Login details
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter your email address",
                "autocomplete": "email",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        ),
    )

    # Keeps the user signed in when selected
    remember_me = forms.BooleanField(
        required=False,
        label="Remember me",
    )
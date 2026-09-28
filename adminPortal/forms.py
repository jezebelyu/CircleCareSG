from django import forms
from django.contrib.auth.models import User

from accounts.models import (
    AppUser,
    EmergencyContact,
    SeniorProfile,
    VolunteerProfile,
)


class AdminSeniorAccountForm(forms.ModelForm):
    class Meta:
        model = AppUser
        fields = [
            "full_name",
            "mobile_number",
            "date_of_birth",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date"}
            ),
        }


class AdminProfileForm(forms.ModelForm):
    email = forms.EmailField(
        label="Email Address",
        required=True,
    )

    class Meta:
        model = AppUser
        fields = [
            "full_name",
            "mobile_number",
            "date_of_birth",
            "profile_picture",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date"}
            ),
            "profile_picture": forms.FileInput(
                attrs={"accept": "image/*"}
            ),
        }

    # Load the email stored in Django's User model.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["email"].initial = self.instance.user.email

    # Check that the new email is not already in use.
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        existing_user = (
            User.objects
            .filter(username__iexact=email)
            .exclude(pk=self.instance.user.pk)
            .exists()
        )

        existing_email = (
            User.objects
            .filter(email__iexact=email)
            .exclude(pk=self.instance.user.pk)
            .exists()
        )

        if existing_user or existing_email:
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    # Update both the AppUser and Django User records.
    def save(self, commit=True):
        app_user = super().save(commit=False)
        django_user = app_user.user

        email = self.cleaned_data["email"].strip().lower()

        django_user.email = email
        django_user.username = email

        if commit:
            django_user.save()
            app_user.save()

        return app_user


class AdminSeniorProfileForm(forms.ModelForm):
    class Meta:
        model = SeniorProfile
        fields = [
            "address",
            "postal_code",
            "unit_number",
            "preferred_language",
            "religion",
            "medical_conditions",
            "allergies",
        ]
        widgets = {
            "medical_conditions": forms.Textarea(
                attrs={"rows": 4}
            ),
            "allergies": forms.Textarea(
                attrs={"rows": 4}
            ),
        }


class AdminAddSeniorForm(forms.Form):
    # Account information
    full_name = forms.CharField(
        max_length=150,
        label="Full Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter senior's full name",
            }
        ),
    )

    nric_fin = forms.CharField(
        max_length=20,
        label="NRIC / FIN",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter NRIC / FIN",
            }
        ),
    )

    mobile_number = forms.CharField(
        max_length=20,
        label="Mobile Number",
        initial="+65",
    )

    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter senior's email address",
            }
        ),
    )

    date_of_birth = forms.DateField(
        label="Date of Birth",
        widget=forms.DateInput(
            attrs={"type": "date"}
        ),
    )

    password = forms.CharField(
        label="Temporary Password",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Minimum 8 characters",
            }
        ),
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Re-enter password",
            }
        ),
    )

    # Address
    address = forms.CharField(
        max_length=255,
        label="Address",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter address",
            }
        ),
    )

    postal_code = forms.CharField(
        max_length=10,
        label="Postal Code",
    )

    unit_number = forms.CharField(
        max_length=20,
        required=False,
        label="Unit / Floor",
    )

    preferred_language = forms.ChoiceField(
        choices=SeniorProfile.LANGUAGE_CHOICES,
        label="Preferred Language",
    )

    # Care information
    religion = forms.CharField(
        max_length=100,
        required=False,
        label="Religion",
    )

    medical_conditions = forms.CharField(
        required=False,
        label="Medical Conditions",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Enter medical conditions, if any",
            }
        ),
    )

    allergies = forms.CharField(
        required=False,
        label="Allergies",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Enter allergies, if any",
            }
        ),
    )

    # Support needs
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
        widget=forms.TextInput(
            attrs={
                "placeholder": "Specify other support",
            }
        ),
    )

    # Emergency contact
    emergency_full_name = forms.CharField(
        max_length=150,
        label="Emergency Contact Name",
    )

    emergency_relationship = forms.CharField(
        max_length=50,
        label="Relationship",
    )

    emergency_mobile_number = forms.CharField(
        max_length=20,
        label="Emergency Contact Number",
        initial="+65",
    )

    # Validation
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    def clean_nric_fin(self):
        nric_fin = self.cleaned_data["nric_fin"].strip().upper()

        if AppUser.objects.filter(nric_fin__iexact=nric_fin).exists():
            raise forms.ValidationError(
                "An account with this NRIC or FIN already exists."
            )

        return nric_fin

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error(
                "confirm_password",
                "The passwords do not match.",
            )

        return cleaned_data


class AdminEmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = [
            "full_name",
            "relationship",
            "mobile_number",
        ]


class AdminVolunteerAccountForm(forms.ModelForm):
    email = forms.EmailField(
        required=False,
        label="Email Address",
    )

    class Meta:
        model = AppUser
        fields = [
            "full_name",
            "mobile_number",
            "date_of_birth",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    # Email is stored on Django's User model.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        app_user = super().save(commit=commit)

        # Update the email stored in Django's User model.
        django_user = app_user.user
        django_user.email = self.cleaned_data.get("email", "")

        if commit:
            django_user.save()

        return app_user


class AdminVolunteerProfileForm(forms.ModelForm):
    class Meta:
        model = VolunteerProfile
        fields = [
            "address",
            "postal_code",
            "unit_number",
            "preferred_language",
            "regular_check_ins",
            "mobility_assistance",
            "meal_assistance",
            "emotional_support",
            "medical_assistance",
            "other_support",
            "transport_available",
            "additional_notes",
            "about_me",
            "skills_interests",
        ]
        widgets = {
            "additional_notes": forms.Textarea(
                attrs={"rows": 4}
            ),
            "about_me": forms.Textarea(
                attrs={"rows": 4}
            ),
            "skills_interests": forms.Textarea(
                attrs={"rows": 4}
            ),
        }


class AdminAddVolunteerForm(forms.Form):
    # Account information
    full_name = forms.CharField(
        max_length=150,
        label="Full Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter volunteer's full name",
            }
        ),
    )

    nric_fin = forms.CharField(
        max_length=20,
        label="NRIC / FIN",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter NRIC / FIN",
            }
        ),
    )

    mobile_number = forms.CharField(
        max_length=20,
        label="Mobile Number",
        initial="+65",
    )

    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter volunteer's email address",
            }
        ),
    )

    date_of_birth = forms.DateField(
        label="Date of Birth",
        widget=forms.DateInput(
            attrs={"type": "date"}
        ),
    )

    password = forms.CharField(
        label="Temporary Password",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Minimum 8 characters",
            }
        ),
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Re-enter password",
            }
        ),
    )

    # Address
    address = forms.CharField(
        max_length=255,
        label="Address",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter address",
            }
        ),
    )

    postal_code = forms.CharField(
        max_length=10,
        label="Postal Code",
    )

    unit_number = forms.CharField(
        max_length=20,
        required=False,
        label="Unit / Floor",
    )

    # Volunteer information
    preferred_language = forms.ChoiceField(
        choices=VolunteerProfile.LANGUAGE_CHOICES,
        label="Preferred Language",
    )

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
        widget=forms.TextInput(
            attrs={
                "placeholder": "Specify other support",
            }
        ),
    )

    transport_available = forms.ChoiceField(
        choices=[
            ("yes", "Yes"),
            ("no", "No"),
        ],
        label="Transport Available",
        widget=forms.RadioSelect,
    )

    additional_notes = forms.CharField(
        required=False,
        label="Additional Notes",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Optional notes about the volunteer",
            }
        ),
    )

    # Validation
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    def clean_nric_fin(self):
        nric_fin = self.cleaned_data["nric_fin"].strip().upper()

        if AppUser.objects.filter(nric_fin__iexact=nric_fin).exists():
            raise forms.ValidationError(
                "An account with this NRIC or FIN already exists."
            )

        return nric_fin

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error(
                "confirm_password",
                "The passwords do not match.",
            )

        return cleaned_data
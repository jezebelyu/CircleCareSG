from django import forms

from accounts.models import GuardianProfile, SeniorProfile


class GuardianProfileForm(forms.Form):
    """Form for editing a Guardian's profile."""

    full_name = forms.CharField(
        max_length=150,
        label="Full Name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your full name",
            }
        ),
    )

    email = forms.EmailField(
        required=False,
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email address",
            }
        ),
    )

    mobile_number = forms.CharField(
        max_length=20,
        label="Mobile Number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your mobile number",
            }
        ),
    )

    profile_picture = forms.ImageField(
        required=False,
        label="Profile Picture",
        widget=forms.FileInput(
            attrs={
                "accept": "image/*",
            }
        ),
    )

    preferred_contact_method = forms.ChoiceField(
        choices=GuardianProfile.CONTACT_METHOD_CHOICES,
        label="Preferred Contact Method",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    preferred_language = forms.ChoiceField(
        choices=GuardianProfile.LANGUAGE_CHOICES,
        label="Preferred Language",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    relationship_to_senior = forms.CharField(
        max_length=50,
        required=False,
        label="Relationship to Senior",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Daughter, Son, Spouse",
            }
        ),
    )


class GuardianSeniorForm(forms.Form):
    """Form for editing the Guardian's linked senior."""

    # Basic information
    full_name = forms.CharField(
        max_length=150,
        label="Full Name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter senior's full name",
            }
        ),
    )

    mobile_number = forms.CharField(
        max_length=20,
        label="Mobile Number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter mobile number",
            }
        ),
    )

    date_of_birth = forms.DateField(
        label="Date of Birth",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    # Address
    address = forms.CharField(
        max_length=255,
        label="Address",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter address",
            }
        ),
    )

    unit_number = forms.CharField(
        max_length=20,
        required=False,
        label="Unit Number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. #05-01",
            }
        ),
    )

    postal_code = forms.CharField(
        max_length=10,
        label="Postal Code",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter postal code",
            }
        ),
    )

    preferred_language = forms.ChoiceField(
        choices=SeniorProfile.LANGUAGE_CHOICES,
        label="Preferred Language",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    # Health information
    allergies = forms.CharField(
        required=False,
        label="Allergies",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter known allergies",
            }
        ),
    )

    medical_conditions = forms.CharField(
        required=False,
        label="Medical Conditions",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter medical conditions",
            }
        ),
    )

    religion = forms.CharField(
        max_length=100,
        required=False,
        label="Religion",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter religion",
            }
        ),
    )

    # Support needs
    regular_check_ins = forms.BooleanField(
        required=False,
        label="Regular Check-Ins",
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
                "class": "form-control",
                "placeholder": "Enter other support needs",
            }
        ),
    )

    # Emergency contact
    emergency_contact_name = forms.CharField(
        max_length=150,
        required=False,
        label="Emergency Contact Name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter emergency contact name",
            }
        ),
    )

    emergency_contact_relationship = forms.CharField(
        max_length=50,
        required=False,
        label="Relationship",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Daughter, Son, Spouse",
            }
        ),
    )

    emergency_contact_mobile = forms.CharField(
        max_length=20,
        required=False,
        label="Emergency Contact Number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter emergency contact number",
            }
        ),
    )

    def clean(self):
        """Require all emergency contact fields when one is provided."""
        cleaned_data = super().clean()

        contact_values = [
            cleaned_data.get("emergency_contact_name"),
            cleaned_data.get("emergency_contact_relationship"),
            cleaned_data.get("emergency_contact_mobile"),
        ]

        if any(contact_values) and not all(contact_values):
            raise forms.ValidationError(
                "Please complete all emergency contact fields."
            )

        return cleaned_data
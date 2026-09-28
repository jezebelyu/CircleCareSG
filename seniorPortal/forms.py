from datetime import date

from django import forms

from accounts.models import AppUser, EmergencyContact, SeniorProfile

from .models import SupportRequest, WellbeingSubmission


class SeniorAccountEditForm(forms.ModelForm):
    class Meta:
        model = AppUser

        fields = [
            "full_name",
            "mobile_number",
            "date_of_birth",
            "profile_picture",
        ]

        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "mobile_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "profile_picture": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
        }


class SeniorProfileEditForm(forms.ModelForm):
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
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "postal_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "unit_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "preferred_language": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "religion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your religion",
                }
            ),
            "medical_conditions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Enter any medical conditions, "
                        "or leave blank"
                    ),
                }
            ),
            "allergies": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Enter any allergies, or leave blank"
                    ),
                }
            ),
        }


class EmergencyContactEditForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact

        fields = [
            "full_name",
            "relationship",
            "mobile_number",
        ]

        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "relationship": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "mobile_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }


class WellbeingSubmissionForm(forms.ModelForm):
    class Meta:
        model = WellbeingSubmission

        fields = [
            "feeling",
            "notes",
        ]

        widgets = {
            "feeling": forms.RadioSelect,
            "notes": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Tell us more about how you are feeling..."
                    ),
                    "rows": 5,
                }
            ),
        }

    def clean_feeling(self):
        feeling = self.cleaned_data.get("feeling")

        if not feeling:
            raise forms.ValidationError(
                "Please select how you are feeling today."
            )

        return feeling


class SupportSelectionForm(forms.Form):
    support_types = forms.MultipleChoiceField(
        choices=SupportRequest.SUPPORT_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Support needed",
    )

    def clean_support_types(self):
        support_types = self.cleaned_data.get(
            "support_types"
        )

        if not support_types:
            raise forms.ValidationError(
                "Please select at least one support type."
            )

        return support_types


class SupportRequestDetailsForm(forms.Form):
    other_support_details = forms.CharField(
        max_length=255,
        required=False,
        label="Please specify other assistance",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Describe the other assistance required",
            }
        ),
    )

    requested_date = forms.DateField(
        label="Request Date",
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    requested_time = forms.TimeField(
        label="Request Time",
        widget=forms.TimeInput(
            attrs={
                "type": "time",
            }
        ),
    )

    additional_notes = forms.CharField(
        required=False,
        label="Additional Notes",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": (
                    "Share any additional information "
                    "about your request"
                ),
            }
        ),
    )

    def clean_requested_date(self):
        requested_date = self.cleaned_data[
            "requested_date"
        ]

        if requested_date < date.today():
            raise forms.ValidationError(
                "The requested date cannot be in the past."
            )

        return requested_date
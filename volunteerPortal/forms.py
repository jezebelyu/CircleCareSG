from django import forms

from accounts.models import (
    AppUser,
    VolunteerDocument,
    VolunteerProfile,
)

from .models import VisitReport


class VolunteerAccountEditForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
            }
        )
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
                    "accept": "image/*",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Email belongs to Django's User model.
        if self.instance and self.instance.user:
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        app_user = super().save(commit=False)

        if commit:
            app_user.save()

            user = app_user.user
            user.email = self.cleaned_data["email"]
            user.save(update_fields=["email"])

        return app_user


class VolunteerProfileEditForm(forms.ModelForm):
    class Meta:
        model = VolunteerProfile
        fields = [
            "about_me",
            "skills_interests",
        ]

        widgets = {
            "about_me": forms.Textarea(
                attrs={
                    "rows": 5,
                }
            ),
            "skills_interests": forms.Textarea(
                attrs={
                    "rows": 5,
                }
            ),
        }


class VolunteerDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = VolunteerDocument
        fields = ["file"]

        widgets = {
            "file": forms.ClearableFileInput(
                attrs={
                    "accept": ".pdf,.jpg,.jpeg,.png",
                }
            ),
        }


class VisitReportForm(forms.ModelForm):
    class Meta:
        model = VisitReport
        fields = [
            "wellbeing_status",
            "assistance_provided",
            "observations",
            "concerns",
            "follow_up_required",
            "follow_up_notes",
        ]

        widgets = {
            "wellbeing_status": forms.Select(),
            "assistance_provided": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Describe the assistance provided during the visit..."
                    ),
                }
            ),
            "observations": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Record any observations about the senior..."
                    ),
                }
            ),
            "concerns": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Describe any concerns noticed during the visit..."
                    ),
                }
            ),
            "follow_up_required": forms.CheckboxInput(),
            "follow_up_notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Describe any follow-up action required..."
                    ),
                }
            ),
        }

        labels = {
            "wellbeing_status": "Senior Wellbeing",
            "assistance_provided": "Assistance Provided",
            "observations": "Observations",
            "concerns": "Concerns",
            "follow_up_required": "Follow-Up Required",
            "follow_up_notes": "Follow-Up Notes",
        }
from django.contrib import admin

from .models import (
    AppUser,
    EmergencyContact,
    GuardianProfile,
    SeniorProfile,
    SeniorVolunteerAssignment,
    VolunteerDocument,
    VolunteerProfile,
)


# User accounts
@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "account_type",
        "mobile_number",
        "date_of_birth",
        "created_at",
    )
    search_fields = ("full_name", "nric_fin", "user__email")
    list_filter = ("account_type", "created_at")


# Senior profiles
@admin.register(SeniorProfile)
class SeniorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "app_user",
        "postal_code",
        "preferred_language",
    )
    search_fields = (
        "app_user__full_name",
        "address",
        "postal_code",
    )


# Guardian profiles
@admin.register(GuardianProfile)
class GuardianProfileAdmin(admin.ModelAdmin):
    list_display = (
        "app_user",
        "linked_senior",
        "relationship_to_senior",
        "preferred_contact_method",
        "preferred_language",
    )
    search_fields = (
        "app_user__full_name",
        "linked_senior__app_user__full_name",
    )
    list_filter = (
        "preferred_contact_method",
        "preferred_language",
    )


# Volunteer profiles
@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "app_user",
        "postal_code",
        "preferred_language",
        "transport_available",
    )
    search_fields = (
        "app_user__full_name",
        "address",
        "postal_code",
    )
    list_filter = (
        "preferred_language",
        "transport_available",
    )


# Senior emergency contacts
@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "relationship",
        "mobile_number",
        "senior",
    )


# Senior and volunteer assignments
@admin.register(SeniorVolunteerAssignment)
class SeniorVolunteerAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "senior",
        "volunteer",
        "assigned_at",
        "active",
    )
    list_filter = ("active", "assigned_at")
    search_fields = (
        "senior__app_user__full_name",
        "volunteer__app_user__full_name",
    )


# Volunteer documents
@admin.register(VolunteerDocument)
class VolunteerDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "volunteer",
        "document_type",
        "uploaded_at",
    )
    list_filter = ("document_type", "uploaded_at")
    search_fields = ("volunteer__app_user__full_name",)
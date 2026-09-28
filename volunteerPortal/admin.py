from django.contrib import admin

from .models import VolunteerAvailability


@admin.register(VolunteerAvailability)
class VolunteerAvailabilityAdmin(admin.ModelAdmin):

    list_display = (
        "volunteer",
        "date",
        "start_time",
        "end_time",
        "available",
    )

    list_filter = (
        "date",
        "available",
    )

    search_fields = (
        "volunteer__app_user__full_name",
    )

    ordering = (
        "date",
        "start_time",
    )
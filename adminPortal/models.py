from django.db import models

from accounts.models import SeniorVolunteerAssignment


class ScheduledVisit(models.Model):
    # Visit options
    STATUS_CHOICES = [
        ("scheduled", "Upcoming"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled / Missed"),
    ]

    VISIT_TYPE_CHOICES = [
        ("home_visit", "Home Visit"),
        ("phone_call", "Phone Call"),
    ]

    VISIT_PURPOSE_CHOICES = [
        ("regular_check_in", "Regular Check-In"),
        ("mobility", "Mobility Assistance"),
        ("meal", "Meal Assistance"),
        ("emotional", "Emotional Support"),
        ("medical", "Medical Assistance"),
        ("other", "Other"),
    ]

    # Assigned senior and volunteer
    assignment = models.ForeignKey(
        SeniorVolunteerAssignment,
        on_delete=models.CASCADE,
        related_name="scheduled_visits",
    )

    # Visit details
    visit_type = models.CharField(
        max_length=30,
        choices=VISIT_TYPE_CHOICES,
        default="home_visit",
    )

    visit_purpose = models.CharField(
        max_length=30,
        choices=VISIT_PURPOSE_CHOICES,
        default="regular_check_in",
    )

    support_types = models.JSONField(
        default=list,
        blank=True,
    )

    other_support_details = models.CharField(
        max_length=255,
        blank=True,
    )

    visit_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    estimated_duration = models.PositiveIntegerField(
        help_text="Estimated duration in minutes.",
        default=60,
    )

    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
    )

    # Record timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "visit_date",
            "start_time",
        ]

    def __str__(self):
        senior_name = self.assignment.senior.app_user.full_name
        volunteer_name = self.assignment.volunteer.app_user.full_name

        return (
            f"{senior_name} with "
            f"{volunteer_name} - "
            f"{self.visit_date}"
        )
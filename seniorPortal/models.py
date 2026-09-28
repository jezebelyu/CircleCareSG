from django.db import models

from accounts.models import SeniorProfile


class WellbeingSubmission(models.Model):
    FEELING_CHOICES = [
        ("great", "Great"),
        ("good", "Good"),
        ("okay", "Okay"),
        ("not_good", "Not Good"),
        ("need_support", "Need Support"),
    ]

    senior = models.ForeignKey(
        SeniorProfile,
        on_delete=models.CASCADE,
        related_name="wellbeing_submissions",
    )

    feeling = models.CharField(
        max_length=20,
        choices=FEELING_CHOICES,
    )

    notes = models.TextField(
        blank=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Alert resolution
    is_resolved = models.BooleanField(
        default=False,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.senior.app_user.full_name} - "
            f"{self.get_feeling_display()}"
        )


class SupportRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("reviewing", "Under Review"),
        ("approved", "Approved"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    SUPPORT_TYPE_CHOICES = [
        ("meal", "Meal Assistance"),
        ("transport", "Transport Assistance"),
        ("emotional", "Emotional Support"),
        ("medical", "Medical Appointment Support"),
        ("other", "Other Assistance"),
    ]

    senior = models.ForeignKey(
        SeniorProfile,
        on_delete=models.CASCADE,
        related_name="support_requests",
    )

    support_types = models.JSONField(
        default=list,
    )

    other_support_details = models.CharField(
        max_length=255,
        blank=True,
    )

    requested_date = models.DateField()

    requested_time = models.TimeField()

    additional_notes = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    admin_notes = models.TextField(
        blank=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def get_support_type_labels(self):
        labels = dict(self.SUPPORT_TYPE_CHOICES)

        return [
            labels.get(value, value)
            for value in self.support_types
        ]

    def __str__(self):
        return (
            f"{self.senior.app_user.full_name} - "
            f"{self.get_status_display()}"
        )
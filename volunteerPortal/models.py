from django.db import models

from accounts.models import VolunteerProfile
from adminPortal.models import ScheduledVisit


class VolunteerAvailability(models.Model):
    volunteer = models.ForeignKey(
        VolunteerProfile,
        on_delete=models.CASCADE,
        related_name="availability_slots",
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    available = models.BooleanField(default=True)

    class Meta:
        ordering = [
            "date",
            "start_time",
        ]
        unique_together = (
            "volunteer",
            "date",
            "start_time",
            "end_time",
        )

    def __str__(self):
        return (
            f"{self.volunteer.app_user.full_name} "
            f"{self.date} "
            f"{self.start_time}-{self.end_time}"
        )


class VisitReport(models.Model):
    WELLBEING_CHOICES = [
        ("good", "Good"),
        ("okay", "Okay"),
        ("concern", "Concern"),
    ]

    visit = models.OneToOneField(
        ScheduledVisit,
        on_delete=models.CASCADE,
        related_name="visit_report",
    )
    wellbeing_status = models.CharField(
        max_length=20,
        choices=WELLBEING_CHOICES,
    )
    assistance_provided = models.TextField()
    observations = models.TextField(blank=True)
    concerns = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "-submitted_at",
        ]

    def __str__(self):
        return (
            f"Report for "
            f"{self.visit.assignment.senior.app_user.full_name} "
            f"on {self.visit.visit_date}"
        )
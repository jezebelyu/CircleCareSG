from django.contrib.auth.models import User
from django.db import models


# Shared user account
class AppUser(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ("senior", "Senior"),
        ("guardian", "Guardian"),
        ("volunteer", "Volunteer"),
        ("admin", "Admin"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="app_profile",
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
    )
    full_name = models.CharField(max_length=150)
    nric_fin = models.CharField(max_length=20, unique=True)
    mobile_number = models.CharField(max_length=20)

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
    )

    date_of_birth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.get_account_type_display()}"


# Senior details and support needs
class SeniorProfile(models.Model):
    LANGUAGE_CHOICES = [
        ("english", "English"),
        ("mandarin", "Mandarin"),
        ("malay", "Malay"),
        ("tamil", "Tamil"),
        ("other", "Other"),
    ]

    app_user = models.OneToOneField(
        AppUser,
        on_delete=models.CASCADE,
        related_name="senior_profile",
    )
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=10)
    unit_number = models.CharField(max_length=20, blank=True)
    preferred_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
    )

    regular_check_ins = models.BooleanField(default=False)
    mobility_assistance = models.BooleanField(default=False)
    meal_assistance = models.BooleanField(default=False)
    emotional_support = models.BooleanField(default=False)
    medical_assistance = models.BooleanField(default=False)
    other_support = models.CharField(max_length=150, blank=True)

    religion = models.CharField(max_length=100, blank=True)
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)

    def __str__(self):
        return f"Senior profile: {self.app_user.full_name}"


# Senior emergency contact
class EmergencyContact(models.Model):
    senior = models.OneToOneField(
        SeniorProfile,
        on_delete=models.CASCADE,
        related_name="emergency_contact",
    )
    full_name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=50)
    mobile_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.full_name} - {self.relationship}"


# Volunteer details and support preferences
class VolunteerProfile(models.Model):
    LANGUAGE_CHOICES = [
        ("english", "English"),
        ("mandarin", "Mandarin"),
        ("malay", "Malay"),
        ("tamil", "Tamil"),
        ("other", "Other"),
    ]

    app_user = models.OneToOneField(
        AppUser,
        on_delete=models.CASCADE,
        related_name="volunteer_profile",
    )
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=10)
    unit_number = models.CharField(max_length=20, blank=True)
    preferred_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
    )

    regular_check_ins = models.BooleanField(default=False)
    mobility_assistance = models.BooleanField(default=False)
    meal_assistance = models.BooleanField(default=False)
    emotional_support = models.BooleanField(default=False)
    medical_assistance = models.BooleanField(default=False)
    other_support = models.CharField(max_length=150, blank=True)

    transport_available = models.BooleanField(default=False)
    additional_notes = models.TextField(blank=True)
    about_me = models.TextField(blank=True)
    skills_interests = models.TextField(blank=True)

    def __str__(self):
        return f"Volunteer profile: {self.app_user.full_name}"


# Documents uploaded by volunteers
class VolunteerDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ("identification", "NRIC / Identification Card"),
        ("first_aid", "First Aid Certificate"),
        ("background", "Background Appointment"),
    ]

    volunteer = models.ForeignKey(
        VolunteerProfile,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
    )
    file = models.FileField(upload_to="volunteer_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["volunteer", "document_type"],
                name="unique_volunteer_document_type",
            )
        ]

    def __str__(self):
        return (
            f"{self.volunteer.app_user.full_name} - "
            f"{self.get_document_type_display()}"
        )


# Links seniors to their assigned volunteers
class SeniorVolunteerAssignment(models.Model):
    senior = models.ForeignKey(
        SeniorProfile,
        on_delete=models.CASCADE,
        related_name="volunteer_assignments",
    )
    volunteer = models.ForeignKey(
        VolunteerProfile,
        on_delete=models.CASCADE,
        related_name="senior_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return (
            f"{self.senior.app_user.full_name} → "
            f"{self.volunteer.app_user.full_name}"
        )


# Guardian details and linked senior
class GuardianProfile(models.Model):
    LANGUAGE_CHOICES = [
        ("english", "English"),
        ("mandarin", "Mandarin"),
        ("malay", "Malay"),
        ("tamil", "Tamil"),
        ("other", "Other"),
    ]

    CONTACT_METHOD_CHOICES = [
        ("phone", "Phone Call"),
        ("sms", "SMS"),
        ("email", "Email"),
    ]

    app_user = models.OneToOneField(
        AppUser,
        on_delete=models.CASCADE,
        related_name="guardian_profile",
    )
    linked_senior = models.ForeignKey(
        SeniorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guardians",
    )
    relationship_to_senior = models.CharField(
        max_length=50,
        blank=True,
    )
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHOD_CHOICES,
        default="phone",
    )
    preferred_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default="english",
    )

    def __str__(self):
        return f"Guardian profile: {self.app_user.full_name}"
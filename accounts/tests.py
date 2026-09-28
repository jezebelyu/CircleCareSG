from datetime import date

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import (
    AppUser,
    EmergencyContact,
    GuardianProfile,
    SeniorProfile,
    SeniorVolunteerAssignment,
    VolunteerDocument,
    VolunteerProfile,
)


class AccountsModelTests(TestCase):

    # Creates a shared AppUser for model tests.
    def create_app_user(
        self,
        username,
        full_name,
        nric_fin,
        account_type,
    ):
        user = User.objects.create_user(
            username=username,
            password="TestPassword123!",
        )

        return AppUser.objects.create(
            user=user,
            account_type=account_type,
            full_name=full_name,
            nric_fin=nric_fin,
            mobile_number="91234567",
            date_of_birth=date(1950, 1, 1),
        )

    # Creates a Senior account and profile for testing.
    def create_senior(self):
        app_user = self.create_app_user(
            username="senior_test",
            full_name="Test Senior",
            nric_fin="S1000001A",
            account_type="senior",
        )

        return SeniorProfile.objects.create(
            app_user=app_user,
            address="123 Test Street",
            postal_code="123456",
            preferred_language="english",
        )

    # Creates a Volunteer account and profile for testing.
    def create_volunteer(self):
        app_user = self.create_app_user(
            username="volunteer_test",
            full_name="Test Volunteer",
            nric_fin="S2000001B",
            account_type="volunteer",
        )

        return VolunteerProfile.objects.create(
            app_user=app_user,
            address="456 Test Street",
            postal_code="654321",
            preferred_language="english",
        )

    # UT01 - Verifies that an AppUser can be created with a valid role.
    def test_app_user_creation_with_valid_role(self):
        app_user = self.create_app_user(
            username="test_user",
            full_name="Test User",
            nric_fin="S3000001C",
            account_type="senior",
        )

        self.assertEqual(app_user.account_type, "senior")
        self.assertEqual(app_user.full_name, "Test User")
        self.assertEqual(AppUser.objects.count(), 1)

    # UT02 - Verifies that duplicate NRIC/FIN values are rejected.
    def test_nric_fin_must_be_unique(self):
        self.create_app_user(
            username="user_one",
            full_name="User One",
            nric_fin="S4000001D",
            account_type="senior",
        )

        second_user = User.objects.create_user(
            username="user_two",
            password="TestPassword123!",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AppUser.objects.create(
                    user=second_user,
                    account_type="volunteer",
                    full_name="User Two",
                    nric_fin="S4000001D",
                    mobile_number="92345678",
                    date_of_birth=date(1980, 1, 1),
                )

    # UT03 - Verifies the relationship between SeniorProfile and AppUser.
    def test_senior_profile_links_to_app_user(self):
        senior = self.create_senior()

        self.assertEqual(senior.app_user.full_name, "Test Senior")
        self.assertEqual(senior.app_user.account_type, "senior")
        self.assertEqual(senior.app_user.senior_profile, senior)

    # UT04 - Verifies that a Senior can be assigned to a Volunteer.
    def test_senior_volunteer_assignment(self):
        senior = self.create_senior()
        volunteer = self.create_volunteer()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
        )

        self.assertEqual(assignment.senior, senior)
        self.assertEqual(assignment.volunteer, volunteer)
        self.assertTrue(assignment.active)

    # UT05 - Verifies that a Guardian can be linked to a Senior.
    def test_guardian_links_to_senior(self):
        senior = self.create_senior()

        guardian_app_user = self.create_app_user(
            username="guardian_test",
            full_name="Test Guardian",
            nric_fin="S5000001E",
            account_type="guardian",
        )

        guardian = GuardianProfile.objects.create(
            app_user=guardian_app_user,
            linked_senior=senior,
            relationship_to_senior="Child",
        )

        self.assertEqual(guardian.linked_senior, senior)
        self.assertIn(guardian, senior.guardians.all())

    # UT06 - Verifies that duplicate Volunteer document types are rejected.
    def test_duplicate_volunteer_document_type_not_allowed(self):
        volunteer = self.create_volunteer()

        VolunteerDocument.objects.create(
            volunteer=volunteer,
            document_type="identification",
            file="volunteer_documents/id_1.pdf",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VolunteerDocument.objects.create(
                    volunteer=volunteer,
                    document_type="identification",
                    file="volunteer_documents/id_2.pdf",
                )

    # UT07 - Verifies the relationship between a Senior and emergency contact.
    def test_emergency_contact_links_to_senior(self):
        senior = self.create_senior()

        emergency_contact = EmergencyContact.objects.create(
            senior=senior,
            full_name="Test Contact",
            relationship="Child",
            mobile_number="98765432",
        )

        self.assertEqual(emergency_contact.senior, senior)
        self.assertEqual(senior.emergency_contact, emergency_contact)
        self.assertEqual(emergency_contact.full_name, "Test Contact")
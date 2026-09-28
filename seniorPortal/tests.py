from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import AppUser, SeniorProfile

from .models import SupportRequest, WellbeingSubmission


class SeniorModelTests(TestCase):

    def create_senior(self):
        user = User.objects.create_user(
            username="senior_test",
            password="TestPassword123!",
        )

        app_user = AppUser.objects.create(
            user=user,
            account_type="senior",
            full_name="Test Senior",
            nric_fin="S6000001F",
            mobile_number="91234567",
            date_of_birth=date(1950, 1, 1),
        )

        return SeniorProfile.objects.create(
            app_user=app_user,
            address="123 Test Street",
            postal_code="123456",
            preferred_language="english",
        )

    # UT08 - Verifies that a wellbeing submission is created correctly.
    def test_wellbeing_submission_creation(self):
        senior = self.create_senior()

        submission = WellbeingSubmission.objects.create(
            senior=senior,
            feeling="good",
            notes="Feeling well today.",
        )

        self.assertEqual(
            submission.senior,
            senior,
        )
        self.assertEqual(
            submission.feeling,
            "good",
        )
        self.assertFalse(
            submission.is_resolved,
        )

    # UT09 - Verifies that a wellbeing submission is linked to its Senior.
    def test_wellbeing_submission_links_to_senior(self):
        senior = self.create_senior()

        submission = WellbeingSubmission.objects.create(
            senior=senior,
            feeling="need_support",
            notes="I need some assistance.",
        )

        self.assertIn(
            submission,
            senior.wellbeing_submissions.all(),
        )

    # UT10 - Verifies that a new support request defaults to pending status.
    def test_support_request_creation_with_default_status(self):
        senior = self.create_senior()

        support_request = SupportRequest.objects.create(
            senior=senior,
            support_types=["meal", "transport"],
            requested_date=date(2026, 10, 1),
            requested_time=time(10, 0),
            additional_notes="Please contact me before the visit.",
        )

        self.assertEqual(
            support_request.senior,
            senior,
        )
        self.assertEqual(
            support_request.status,
            "pending",
        )
        self.assertEqual(
            support_request.support_types,
            ["meal", "transport"],
        )

    # UT11 - Verifies that support type values return the correct labels.
    def test_support_request_returns_correct_support_type_labels(self):
        senior = self.create_senior()

        support_request = SupportRequest.objects.create(
            senior=senior,
            support_types=["meal", "emotional"],
            requested_date=date(2026, 10, 1),
            requested_time=time(14, 0),
        )

        self.assertEqual(
            support_request.get_support_type_labels(),
            [
                "Meal Assistance",
                "Emotional Support",
            ],
        )


class SeniorViewTests(TestCase):

    def create_user(
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

        app_user = AppUser.objects.create(
            user=user,
            account_type=account_type,
            full_name=full_name,
            nric_fin=nric_fin,
            mobile_number="91234567",
            date_of_birth=date(1950, 1, 1),
        )

        return user, app_user

    def create_senior_user(self):
        user, app_user = self.create_user(
            username="senior_view_test",
            full_name="Test Senior",
            nric_fin="S6100001F",
            account_type="senior",
        )

        SeniorProfile.objects.create(
            app_user=app_user,
            address="123 Test Street",
            postal_code="123456",
            preferred_language="english",
        )

        return user

    # VT01 - Verifies that unauthenticated users cannot access the Senior Dashboard.
    def test_unauthenticated_user_cannot_access_senior_dashboard(self):
        response = self.client.get(
            reverse("senior_dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertIn(
            reverse("login"),
            response.url,
        )

    # VT02 - Verifies that a Senior can access the Senior Dashboard.
    def test_senior_can_access_senior_dashboard(self):
        user = self.create_senior_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("senior_dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertTemplateUsed(
            response,
            "seniorPortal/dashboard.html",
        )

    # VT03 - Verifies that non-Senior users cannot access the Senior Dashboard.
    def test_non_senior_cannot_access_senior_dashboard(self):
        user, app_user = self.create_user(
            username="volunteer_view_test",
            full_name="Test Volunteer",
            nric_fin="S6200001G",
            account_type="volunteer",
        )

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("senior_dashboard")
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    # VT04 - Verifies that a Senior can access the wellbeing check-in page.
    def test_senior_can_access_wellbeing_page(self):
        user = self.create_senior_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("senior_wellbeing")
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertTemplateUsed(
            response,
            "seniorPortal/wellbeing.html",
        )

    # VT05 - Verifies that a Senior can submit a wellbeing check-in.
    def test_senior_can_submit_wellbeing_update(self):
        user = self.create_senior_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse("senior_wellbeing"),
            {
                "feeling": "good",
                "notes": "Feeling well today.",
            },
        )

        self.assertRedirects(
            response,
            reverse("check_in_history"),
        )
        self.assertEqual(
            WellbeingSubmission.objects.count(),
            1,
        )

        submission = WellbeingSubmission.objects.first()

        self.assertEqual(
            submission.feeling,
            "good",
        )
        self.assertEqual(
            submission.senior.app_user.user,
            user,
        )

    # VT06 - Verifies that selected support types are saved between form steps.
    def test_support_request_step_one_saves_selection_in_session(self):
        user = self.create_senior_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse("support_request_select"),
            {
                "support_types": [
                    "meal",
                    "emotional",
                ],
            },
        )

        self.assertRedirects(
            response,
            reverse("support_request_details"),
        )

        session = self.client.session

        self.assertEqual(
            session["selected_support_types"],
            [
                "meal",
                "emotional",
            ],
        )

    # VT07 - Verifies that a Senior can complete and submit a support request.
    def test_senior_can_complete_support_request(self):
        user = self.create_senior_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        session = self.client.session
        session["selected_support_types"] = [
            "meal",
            "emotional",
        ]
        session.save()

        response = self.client.post(
            reverse("support_request_details"),
            {
                "requested_date": "2026-10-10",
                "requested_time": "10:00",
                "other_support_details": "",
                "additional_notes": "Please contact me first.",
            },
        )

        self.assertRedirects(
            response,
            reverse("support_request_history"),
        )
        self.assertEqual(
            SupportRequest.objects.count(),
            1,
        )

        support_request = SupportRequest.objects.first()

        self.assertEqual(
            support_request.support_types,
            [
                "meal",
                "emotional",
            ],
        )
        self.assertEqual(
            support_request.status,
            "pending",
        )
        self.assertEqual(
            support_request.senior.app_user.user,
            user,
        )
        self.assertNotIn(
            "selected_support_types",
            self.client.session,
        )

    # VT08 - Verifies that support request details cannot be accessed before step one.
    def test_support_request_details_requires_step_one(self):
        user = self.create_senior_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("support_request_details")
        )

        self.assertRedirects(
            response,
            reverse("support_request_select"),
        )
        self.assertEqual(
            SupportRequest.objects.count(),
            0,
        )

    # VT09 - Verifies that Other Assistance requires a description.
    def test_other_support_requires_description(self):
        user = self.create_senior_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        session = self.client.session
        session["selected_support_types"] = ["other"]
        session.save()

        response = self.client.post(
            reverse("support_request_details"),
            {
                "requested_date": "2026-10-10",
                "requested_time": "10:00",
                "other_support_details": "",
                "additional_notes": "",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            SupportRequest.objects.count(),
            0,
        )
        self.assertFormError(
            response.context["form"],
            "other_support_details",
            "Please describe the other assistance needed.",
        )
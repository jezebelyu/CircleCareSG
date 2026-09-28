from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import (
    AppUser,
    GuardianProfile,
    SeniorProfile,
    SeniorVolunteerAssignment,
    VolunteerProfile,
)
from adminPortal.models import ScheduledVisit
from seniorPortal.models import WellbeingSubmission
from volunteerPortal.models import VisitReport


class GuardianPortalTests(TestCase):

    def setUp(self):
        # Guardian account
        self.guardian_user = User.objects.create_user(
            username="guardian_test",
            password="Test12345!",
            email="guardian@example.com",
        )

        self.guardian_app_user = AppUser.objects.create(
            user=self.guardian_user,
            account_type="guardian",
            full_name="Test Guardian",
            nric_fin="G1234567A",
            mobile_number="91234567",
            date_of_birth=date(1980, 1, 1),
        )

        # Linked senior
        self.senior_user = User.objects.create_user(
            username="senior_test",
            password="Test12345!",
        )

        self.senior_app_user = AppUser.objects.create(
            user=self.senior_user,
            account_type="senior",
            full_name="Test Senior",
            nric_fin="S1234567A",
            mobile_number="92345678",
            date_of_birth=date(1950, 1, 1),
        )

        self.senior = SeniorProfile.objects.create(
            app_user=self.senior_app_user,
            address="123 Test Street",
            postal_code="123456",
            unit_number="#01-01",
            preferred_language="english",
            regular_check_ins=True,
        )

        self.guardian = GuardianProfile.objects.create(
            app_user=self.guardian_app_user,
            linked_senior=self.senior,
            relationship_to_senior="Daughter",
            preferred_contact_method="phone",
            preferred_language="english",
        )

        # Volunteer account
        self.volunteer_user = User.objects.create_user(
            username="volunteer_test",
            password="Test12345!",
        )

        self.volunteer_app_user = AppUser.objects.create(
            user=self.volunteer_user,
            account_type="volunteer",
            full_name="Test Volunteer",
            nric_fin="V1234567A",
            mobile_number="93456789",
            date_of_birth=date(1990, 1, 1),
        )

        self.volunteer = VolunteerProfile.objects.create(
            app_user=self.volunteer_app_user,
            address="456 Volunteer Street",
            postal_code="654321",
            preferred_language="english",
        )

        # Senior-volunteer assignment
        self.assignment = SeniorVolunteerAssignment.objects.create(
            senior=self.senior,
            volunteer=self.volunteer,
            active=True,
        )

        self.client.login(
            username="guardian_test",
            password="Test12345!",
        )

    # GP01 - Verifies that a Guardian can access the Dashboard and linked Senior data.
    def test_guardian_can_access_dashboard(self):
        response = self.client.get(
            reverse("guardian_dashboard")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "guardianPortal/dashboard.html",
        )
        self.assertEqual(
            response.context["linked_senior"],
            self.senior,
        )

    # GP02 - Verifies that unauthenticated users cannot access the Guardian Dashboard.
    def test_unauthenticated_user_cannot_access_dashboard(self):
        self.client.logout()

        response = self.client.get(
            reverse("guardian_dashboard")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("login"),
            response.url,
        )

    # GP03 - Verifies that non-Guardian users cannot access the Guardian Portal.
    def test_non_guardian_cannot_access_guardian_portal(self):
        self.client.logout()

        self.client.login(
            username="senior_test",
            password="Test12345!",
        )

        response = self.client.get(
            reverse("guardian_dashboard")
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    # GP04 - Verifies that a Guardian can view their linked Senior.
    def test_guardian_can_view_linked_senior(self):
        response = self.client.get(
            reverse("guardian_my_senior")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["linked_senior"],
            self.senior,
        )

    # GP05 - Verifies that a Guardian can view the Volunteer assigned to their linked Senior.
    def test_guardian_can_view_assigned_volunteer(self):
        response = self.client.get(
            reverse("guardian_contact_volunteer")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["assigned_volunteer"],
            self.volunteer,
        )
        self.assertEqual(
            response.context["active_assignment"],
            self.assignment,
        )

    # GP06 - Verifies that a Guardian can view their linked Senior's check-in reports.
    def test_guardian_can_view_check_in_reports(self):
        wellbeing = WellbeingSubmission.objects.create(
            senior=self.senior,
            feeling="good",
            notes="Feeling well today.",
        )

        response = self.client.get(
            reverse("guardian_check_in_reports")
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            wellbeing,
            response.context["wellbeing_submissions"],
        )

    # GP07 - Verifies that check-in reports exclude data belonging to other Seniors.
    def test_check_in_reports_excludes_other_senior_data(self):
        linked_submission = WellbeingSubmission.objects.create(
            senior=self.senior,
            feeling="good",
            notes="Linked Senior submission.",
        )

        other_user = User.objects.create_user(
            username="other_senior",
            password="Test12345!",
        )

        other_app_user = AppUser.objects.create(
            user=other_user,
            account_type="senior",
            full_name="Other Senior",
            nric_fin="S7654321A",
            mobile_number="94567890",
            date_of_birth=date(1955, 1, 1),
        )

        other_senior = SeniorProfile.objects.create(
            app_user=other_app_user,
            address="789 Other Street",
            postal_code="987654",
            preferred_language="english",
        )

        other_submission = WellbeingSubmission.objects.create(
            senior=other_senior,
            feeling="need_support",
            notes="Other Senior submission.",
        )

        response = self.client.get(
            reverse("guardian_check_in_reports")
        )

        submissions = response.context["wellbeing_submissions"]

        self.assertEqual(response.status_code, 200)
        self.assertIn(linked_submission, submissions)
        self.assertNotIn(other_submission, submissions)

    # GP08 - Verifies that the Dashboard uses wellbeing data from the linked Senior.
    def test_dashboard_uses_linked_senior_wellbeing(self):
        linked_submission = WellbeingSubmission.objects.create(
            senior=self.senior,
            feeling="good",
            notes="Linked Senior wellbeing.",
        )

        response = self.client.get(
            reverse("guardian_dashboard")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["latest_wellbeing"],
            linked_submission,
        )

    # GP09 - Verifies that a need-support check-in creates a high-priority Guardian alert.
    def test_guardian_alerts_include_high_priority_wellbeing(self):
        WellbeingSubmission.objects.create(
            senior=self.senior,
            feeling="need_support",
            notes="Please contact me.",
        )

        response = self.client.get(
            reverse("guardian_alerts")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["high_priority_count"],
            1,
        )

        alerts = response.context["alerts"]

        self.assertTrue(
            any(
                alert["priority"] == "high"
                and alert["source"] == "wellbeing"
                for alert in alerts
            )
        )
    # GP10 - Verifies that a cancelled visit creates a medium-priority Guardian alert.
    def test_cancelled_visit_creates_guardian_alert(self):
        ScheduledVisit.objects.create(
            assignment=self.assignment,
            visit_type="home_visit",
            visit_purpose="regular_check_in",
            visit_date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status="cancelled",
        )

        response = self.client.get(
            reverse("guardian_alerts")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["medium_priority_count"],
            1,
        )

        alerts = response.context["alerts"]

        self.assertTrue(
            any(
                alert["source"] == "visit"
                and alert["priority"] == "medium"
                for alert in alerts
            )
        )

    # GP11 - Verifies that a Guardian can view a Volunteer report for their linked Senior.
    def test_guardian_can_view_volunteer_report(self):
        visit = ScheduledVisit.objects.create(
            assignment=self.assignment,
            visit_type="home_visit",
            visit_purpose="regular_check_in",
            visit_date=date.today() - timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status="completed",
        )

        report = VisitReport.objects.create(
            visit=visit,
            wellbeing_status="good",
            assistance_provided="Regular check-in completed.",
            observations="Senior was well.",
        )

        response = self.client.get(
            reverse(
                "guardian_view_volunteer_report",
                args=[report.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["report"],
            report,
        )

    # GP12 - Verifies that a Guardian can access their own profile.
    def test_guardian_can_access_profile(self):
        response = self.client.get(
            reverse("guardian_profile")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "guardianPortal/profile.html",
        )
        self.assertEqual(
            response.context["guardian_profile"],
            self.guardian,
        )
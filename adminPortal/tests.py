from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import (
    AppUser,
    SeniorProfile,
    SeniorVolunteerAssignment,
    VolunteerProfile,
)
from seniorPortal.models import SupportRequest, WellbeingSubmission
from volunteerPortal.models import VisitReport, VolunteerAvailability

from .models import ScheduledVisit


class AdminModelTests(TestCase):

    # Creates an AppUser for Admin tests.
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
            date_of_birth=date(1980, 1, 1),
        )

    # Creates a Senior-Volunteer assignment for scheduled visit tests.
    def create_assignment(self):
        senior_app_user = self.create_app_user(
            username="senior_test",
            full_name="Test Senior",
            nric_fin="S9000001J",
            account_type="senior",
        )

        senior = SeniorProfile.objects.create(
            app_user=senior_app_user,
            address="123 Test Street",
            postal_code="123456",
            preferred_language="english",
        )

        volunteer_app_user = self.create_app_user(
            username="volunteer_test",
            full_name="Test Volunteer",
            nric_fin="S9000002K",
            account_type="volunteer",
        )

        volunteer = VolunteerProfile.objects.create(
            app_user=volunteer_app_user,
            address="456 Test Street",
            postal_code="654321",
            preferred_language="english",
        )

        return SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
        )

    # UT16 - Verifies that a scheduled visit is created with the correct defaults.
    def test_scheduled_visit_creation_with_defaults(self):
        assignment = self.create_assignment()

        visit = ScheduledVisit.objects.create(
            assignment=assignment,
            visit_date=date(2026, 10, 5),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )

        self.assertEqual(visit.assignment, assignment)
        self.assertEqual(visit.status, "scheduled")
        self.assertEqual(visit.visit_type, "home_visit")
        self.assertEqual(visit.visit_purpose, "regular_check_in")
        self.assertEqual(visit.estimated_duration, 60)

    # UT17 - Verifies that a scheduled visit is linked to its Senior-Volunteer assignment.
    def test_scheduled_visit_links_to_assignment(self):
        assignment = self.create_assignment()

        visit = ScheduledVisit.objects.create(
            assignment=assignment,
            visit_type="phone_call",
            visit_purpose="emotional",
            support_types=["emotional"],
            visit_date=date(2026, 10, 6),
            start_time=time(14, 0),
            end_time=time(15, 0),
            estimated_duration=60,
            notes="Provide emotional support.",
        )

        self.assertIn(
            visit,
            assignment.scheduled_visits.all(),
        )
        self.assertEqual(
            visit.assignment.senior.app_user.full_name,
            "Test Senior",
        )
        self.assertEqual(
            visit.assignment.volunteer.app_user.full_name,
            "Test Volunteer",
        )
        self.assertEqual(visit.visit_type, "phone_call")
        self.assertEqual(visit.visit_purpose, "emotional")


class AdminViewTests(TestCase):

    # Test data helpers
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

        app_user = AppUser.objects.create(
            user=user,
            account_type=account_type,
            full_name=full_name,
            nric_fin=nric_fin,
            mobile_number="91234567",
            date_of_birth=date(1980, 1, 1),
        )

        return user, app_user

    def create_admin_user(self):
        user, app_user = self.create_app_user(
            username="admin_view_test",
            full_name="Test Admin",
            nric_fin="S9100001J",
            account_type="admin",
        )

        return user

    def create_senior_user(self):
        user, app_user = self.create_app_user(
            username="senior_admin_test",
            full_name="Test Senior",
            nric_fin="S9200001K",
            account_type="senior",
        )

        senior = SeniorProfile.objects.create(
            app_user=app_user,
            address="123 Test Street",
            postal_code="123456",
            preferred_language="english",
        )

        return user, senior

    def create_volunteer_user(self):
        user, app_user = self.create_app_user(
            username="volunteer_admin_test",
            full_name="Test Volunteer",
            nric_fin="S9300001L",
            account_type="volunteer",
        )

        volunteer = VolunteerProfile.objects.create(
            app_user=app_user,
            address="456 Test Street",
            postal_code="654321",
            preferred_language="english",
        )

        return user, volunteer

    # VT22 - Verifies that unauthenticated users cannot access the Admin Dashboard.
    def test_unauthenticated_user_cannot_access_admin_dashboard(self):
        response = self.client.get(
            reverse("admin_dashboard")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("login"),
            response.url,
        )

    # VT23 - Verifies that an Admin can access the Admin Dashboard.
    def test_admin_can_access_admin_dashboard(self):
        user = self.create_admin_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("admin_dashboard")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "adminPortal/dashboard.html",
        )

    # VT24 - Verifies that non-Admin users cannot access the Admin Dashboard.
    def test_non_admin_cannot_access_admin_dashboard(self):
        user, senior = self.create_senior_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("admin_dashboard")
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    # VT25 - Verifies that an Admin can assign a Senior to a Volunteer.
    def test_admin_can_assign_senior_to_volunteer(self):
        admin_user = self.create_admin_user()
        senior_user, senior = self.create_senior_user()
        volunteer_user, volunteer = self.create_volunteer_user()

        self.client.login(
            username=admin_user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "admin_assign_senior_to_volunteer",
                args=[volunteer.pk],
            ),
            {
                "senior_id": senior.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "admin_volunteer_detail",
                args=[volunteer.pk],
            ),
        )

        self.assertEqual(
            SeniorVolunteerAssignment.objects.count(),
            1,
        )

        assignment = SeniorVolunteerAssignment.objects.first()

        self.assertEqual(assignment.senior, senior)
        self.assertEqual(assignment.volunteer, volunteer)
        self.assertTrue(assignment.active)

    # VT26 - Verifies that reassigning a Senior deactivates the previous assignment.
    def test_reassigning_senior_deactivates_previous_assignment(self):
        admin_user = self.create_admin_user()
        senior_user, senior = self.create_senior_user()
        volunteer_user_1, volunteer_1 = self.create_volunteer_user()

        # The helper uses fixed username and NRIC values.
        user_2, app_user_2 = self.create_app_user(
            username="volunteer_admin_test_2",
            full_name="Second Volunteer",
            nric_fin="S9400001M",
            account_type="volunteer",
        )

        volunteer_2 = VolunteerProfile.objects.create(
            app_user=app_user_2,
            address="789 Test Street",
            postal_code="765432",
            preferred_language="english",
        )

        old_assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer_1,
            active=True,
        )

        self.client.login(
            username=admin_user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "admin_assign_senior_to_volunteer",
                args=[volunteer_2.pk],
            ),
            {
                "senior_id": senior.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "admin_volunteer_detail",
                args=[volunteer_2.pk],
            ),
        )

        old_assignment.refresh_from_db()
        self.assertFalse(old_assignment.active)

        new_assignment = SeniorVolunteerAssignment.objects.get(
            senior=senior,
            volunteer=volunteer_2,
        )

        self.assertTrue(new_assignment.active)

        self.assertEqual(
            SeniorVolunteerAssignment.objects.filter(
                senior=senior,
                active=True,
            ).count(),
            1,
        )

    # VT27 - Verifies that an Admin can remove a Senior from a Volunteer assignment.
    def test_admin_can_remove_senior_from_volunteer(self):
        admin_user = self.create_admin_user()
        senior_user, senior = self.create_senior_user()
        volunteer_user, volunteer = self.create_volunteer_user()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
            active=True,
        )

        self.client.login(
            username=admin_user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "admin_remove_senior_from_volunteer",
                args=[assignment.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "admin_volunteer_detail",
                args=[volunteer.pk],
            ),
        )

        assignment.refresh_from_db()
        self.assertFalse(assignment.active)

        # Keep the assignment for historical records.
        self.assertTrue(
            SeniorVolunteerAssignment.objects.filter(
                pk=assignment.pk
            ).exists()
        )

    # VT28 - Verifies that an Admin can schedule a visit using Volunteer availability.
    def test_admin_can_schedule_visit(self):
        admin_user = self.create_admin_user()
        senior_user, senior = self.create_senior_user()
        volunteer_user, volunteer = self.create_volunteer_user()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
            active=True,
        )

        availability = VolunteerAvailability.objects.create(
            volunteer=volunteer,
            date=date(2026, 10, 20),
            start_time=time(9, 0),
            end_time=time(11, 0),
            available=True,
        )

        self.client.login(
            username=admin_user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse("admin_schedule_visit"),
            {
                "assignment_id": assignment.pk,
                "availability_id": availability.pk,
                "visit_type": "home_visit",
                "visit_purpose": "regular_check_in",
                "support_types": ["emotional"],
                "other_support_details": "",
                "estimated_duration": "60",
                "notes": "Scheduled by admin.",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin_visits_schedule"),
        )

        self.assertEqual(
            ScheduledVisit.objects.count(),
            1,
        )

        visit = ScheduledVisit.objects.first()

        self.assertEqual(visit.assignment, assignment)
        self.assertEqual(
            visit.visit_date,
            date(2026, 10, 20),
        )
        self.assertEqual(
            visit.start_time,
            time(9, 0),
        )
        self.assertEqual(
            visit.end_time,
            time(10, 0),
        )
        self.assertEqual(visit.status, "scheduled")

    # VT29 - Verifies that an Admin cannot use availability belonging to another Volunteer.
    def test_admin_cannot_use_wrong_volunteer_availability(self):
        admin_user = self.create_admin_user()
        senior_user, senior = self.create_senior_user()
        volunteer_user, volunteer = self.create_volunteer_user()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
            active=True,
        )

        user_2, app_user_2 = self.create_app_user(
            username="second_volunteer_test",
            full_name="Second Volunteer",
            nric_fin="S9500001N",
            account_type="volunteer",
        )

        volunteer_2 = VolunteerProfile.objects.create(
            app_user=app_user_2,
            address="789 Test Street",
            postal_code="765432",
            preferred_language="english",
        )

        wrong_availability = VolunteerAvailability.objects.create(
            volunteer=volunteer_2,
            date=date(2026, 10, 20),
            start_time=time(9, 0),
            end_time=time(11, 0),
            available=True,
        )

        self.client.login(
            username=admin_user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse("admin_schedule_visit"),
            {
                "assignment_id": assignment.pk,
                "availability_id": wrong_availability.pk,
                "visit_type": "home_visit",
                "visit_purpose": "regular_check_in",
                "support_types": ["emotional"],
                "estimated_duration": "60",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            ScheduledVisit.objects.count(),
            0,
        )

    # VT30 - Verifies that an Admin cannot double-book a Volunteer availability slot.
    def test_admin_cannot_double_book_volunteer_slot(self):
        admin_user = self.create_admin_user()
        senior_user, senior = self.create_senior_user()
        volunteer_user, volunteer = self.create_volunteer_user()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
            active=True,
        )

        availability = VolunteerAvailability.objects.create(
            volunteer=volunteer,
            date=date(2026, 10, 20),
            start_time=time(9, 0),
            end_time=time(11, 0),
            available=True,
        )

        ScheduledVisit.objects.create(
            assignment=assignment,
            visit_date=date(2026, 10, 20),
            start_time=time(9, 0),
            end_time=time(10, 0),
            visit_type="home_visit",
            visit_purpose="regular_check_in",
            status="scheduled",
        )

        self.client.login(
            username=admin_user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse("admin_schedule_visit"),
            {
                "assignment_id": assignment.pk,
                "availability_id": availability.pk,
                "visit_type": "home_visit",
                "visit_purpose": "regular_check_in",
                "support_types": ["emotional"],
                "estimated_duration": "60",
                "notes": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin_schedule_visit"),
        )

        # The existing visit should remain unchanged.
        self.assertEqual(
            ScheduledVisit.objects.count(),
            1,
        )

    # VT31 - Verifies that an Admin can update and approve a support request.
    def test_admin_can_update_support_request(self):
        admin_user = self.create_admin_user()
        senior_user, senior = self.create_senior_user()

        support_request = SupportRequest.objects.create(
            senior=senior,
            support_types=["emotional"],
            requested_date=date(2026, 10, 20),
            requested_time=time(10, 0),
            status="pending",
        )

        self.client.login(
            username=admin_user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "admin_support_request_detail",
                args=[support_request.pk],
            ),
            {
                "status": "approved",
                "admin_notes": "Request reviewed and approved.",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "admin_support_request_detail",
                args=[support_request.pk],
            ),
        )

        support_request.refresh_from_db()

        self.assertEqual(
            support_request.status,
            "approved",
        )
        self.assertEqual(
            support_request.admin_notes,
            "Request reviewed and approved.",
        )

    # VT32 - Verifies that an invalid support request status is rejected.
    def test_admin_cannot_set_invalid_support_request_status(self):
        admin_user = self.create_admin_user()
        senior_user, senior = self.create_senior_user()

        support_request = SupportRequest.objects.create(
            senior=senior,
            support_types=["emotional"],
            requested_date=date(2026, 10, 20),
            requested_time=time(10, 0),
            status="pending",
        )

        self.client.login(
            username=admin_user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "admin_support_request_detail",
                args=[support_request.pk],
            ),
            {
                "status": "invalid_status",
                "admin_notes": "This should not be saved.",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "admin_support_request_detail",
                args=[support_request.pk],
            ),
        )

        support_request.refresh_from_db()

        self.assertEqual(
            support_request.status,
            "pending",
        )
        self.assertNotEqual(
            support_request.admin_notes,
            "This should not be saved.",
        )

    # VT33 - Verifies that an Admin can resolve a Senior wellbeing alert.
    def test_admin_can_resolve_wellbeing_alert(self):
        admin_user = self.create_admin_user()
        senior_user, senior = self.create_senior_user()

        submission = WellbeingSubmission.objects.create(
            senior=senior,
            feeling="need_support",
            notes="I need some assistance today.",
        )

        self.assertFalse(submission.is_resolved)

        self.client.login(
            username=admin_user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "admin_alert_detail",
                args=[submission.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("admin_alerts"),
        )

        submission.refresh_from_db()

        self.assertTrue(submission.is_resolved)
        self.assertIsNotNone(submission.resolved_at)
import json
from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import (
    AppUser,
    SeniorProfile,
    SeniorVolunteerAssignment,
    VolunteerProfile,
)
from adminPortal.models import ScheduledVisit

from .models import VisitReport, VolunteerAvailability


class VolunteerModelTests(TestCase):

    # Creates an AppUser for Volunteer model tests.
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

    # Creates a Volunteer profile for testing.
    def create_volunteer(self):
        app_user = self.create_app_user(
            username="volunteer_test",
            full_name="Test Volunteer",
            nric_fin="S7000001G",
            account_type="volunteer",
        )

        return VolunteerProfile.objects.create(
            app_user=app_user,
            address="456 Test Street",
            postal_code="654321",
            preferred_language="english",
        )

    # Creates a Senior profile for testing.
    def create_senior(self):
        app_user = self.create_app_user(
            username="senior_test",
            full_name="Test Senior",
            nric_fin="S8000001H",
            account_type="senior",
        )

        return SeniorProfile.objects.create(
            app_user=app_user,
            address="123 Test Street",
            postal_code="123456",
            preferred_language="english",
        )

    # Creates a scheduled visit with an assigned Senior and Volunteer.
    def create_scheduled_visit(self):
        senior = self.create_senior()
        volunteer = self.create_volunteer()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
        )

        return ScheduledVisit.objects.create(
            assignment=assignment,
            visit_date=date(2026, 10, 1),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )

    # UT12 - Verifies that a Volunteer availability slot is created correctly.
    def test_volunteer_availability_creation(self):
        volunteer = self.create_volunteer()

        availability = VolunteerAvailability.objects.create(
            volunteer=volunteer,
            date=date(2026, 10, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
        )

        self.assertEqual(
            availability.volunteer,
            volunteer,
        )

        self.assertTrue(
            availability.available,
        )

        self.assertIn(
            availability,
            volunteer.availability_slots.all(),
        )

    # UT13 - Verifies that duplicate Volunteer availability slots are rejected.
    def test_duplicate_volunteer_availability_not_allowed(self):
        volunteer = self.create_volunteer()

        VolunteerAvailability.objects.create(
            volunteer=volunteer,
            date=date(2026, 10, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VolunteerAvailability.objects.create(
                    volunteer=volunteer,
                    date=date(2026, 10, 1),
                    start_time=time(9, 0),
                    end_time=time(12, 0),
                )

    # UT14 - Verifies that a visit report is linked to its scheduled visit.
    def test_visit_report_links_to_scheduled_visit(self):
        visit = self.create_scheduled_visit()

        report = VisitReport.objects.create(
            visit=visit,
            wellbeing_status="good",
            assistance_provided="Completed regular check-in.",
            observations="Senior appeared well.",
        )

        self.assertEqual(
            report.visit,
            visit,
        )

        self.assertEqual(
            visit.visit_report,
            report,
        )

        self.assertFalse(
            report.follow_up_required,
        )

    # UT15 - Verifies that only one visit report is allowed per scheduled visit.
    def test_only_one_report_allowed_per_visit(self):
        visit = self.create_scheduled_visit()

        VisitReport.objects.create(
            visit=visit,
            wellbeing_status="good",
            assistance_provided="Completed regular check-in.",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VisitReport.objects.create(
                    visit=visit,
                    wellbeing_status="okay",
                    assistance_provided="Second report.",
                )


class VolunteerViewTests(TestCase):

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

    def create_volunteer_user(
        self,
        username="volunteer_view_test",
        nric_fin="S7100001G",
    ):
        user, app_user = self.create_app_user(
            username=username,
            full_name="Test Volunteer",
            nric_fin=nric_fin,
            account_type="volunteer",
        )

        volunteer = VolunteerProfile.objects.create(
            app_user=app_user,
            address="456 Test Street",
            postal_code="654321",
            preferred_language="english",
        )

        return user, volunteer

    def create_senior(
        self,
        username="senior_view_test",
        nric_fin="S8100001H",
    ):
        user, app_user = self.create_app_user(
            username=username,
            full_name="Test Senior",
            nric_fin=nric_fin,
            account_type="senior",
        )

        senior = SeniorProfile.objects.create(
            app_user=app_user,
            address="123 Test Street",
            postal_code="123456",
            preferred_language="english",
        )

        return user, senior

    # VT10 - Verifies that unauthenticated users cannot access the Volunteer Dashboard.
    def test_unauthenticated_user_cannot_access_volunteer_dashboard(self):
        response = self.client.get(
            reverse("volunteer_dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            reverse("login"),
            response.url,
        )

    # VT11 - Verifies that a Volunteer can access the Volunteer Dashboard.
    def test_volunteer_can_access_volunteer_dashboard(self):
        user, volunteer = self.create_volunteer_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("volunteer_dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "volunteerPortal/dashboard.html",
        )

    # VT12 - Verifies that non-Volunteer users cannot access the Volunteer Dashboard.
    def test_non_volunteer_cannot_access_volunteer_dashboard(self):
        user, senior = self.create_senior()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("volunteer_dashboard")
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    # VT13 - Verifies that a Volunteer cannot view an unassigned Senior.
    def test_volunteer_cannot_view_unassigned_senior(self):
        volunteer_user, volunteer = self.create_volunteer_user()
        senior_user, senior = self.create_senior()

        self.client.login(
            username=volunteer_user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "volunteer_senior_detail",
                args=[senior.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    # VT14 - Verifies that a Volunteer can save availability slots.
    def test_volunteer_can_save_availability(self):
        user, volunteer = self.create_volunteer_user()

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse("volunteer_availability")
            + "?week=2026-10-05",
            {
                "selected_slots": json.dumps([
                    {
                        "date": "2026-10-05",
                        "start": "09:00",
                        "end": "10:00",
                    },
                    {
                        "date": "2026-10-06",
                        "start": "14:00",
                        "end": "15:00",
                    },
                ]),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            VolunteerAvailability.objects.filter(
                volunteer=volunteer
            ).count(),
            2,
        )

        first_slot = VolunteerAvailability.objects.get(
            volunteer=volunteer,
            date=date(2026, 10, 5),
        )

        self.assertEqual(
            first_slot.start_time,
            time(9, 0),
        )

        self.assertEqual(
            first_slot.end_time,
            time(10, 0),
        )

        self.assertTrue(
            first_slot.available
        )

    # VT15 - Verifies that saving availability replaces existing slots for the same week.
    def test_saving_availability_replaces_existing_week_slots(self):
        user, volunteer = self.create_volunteer_user()

        VolunteerAvailability.objects.create(
            volunteer=volunteer,
            date=date(2026, 10, 5),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        self.client.post(
            reverse("volunteer_availability")
            + "?week=2026-10-05",
            {
                "selected_slots": json.dumps([
                    {
                        "date": "2026-10-07",
                        "start": "13:00",
                        "end": "14:00",
                    },
                ]),
            },
        )

        self.assertFalse(
            VolunteerAvailability.objects.filter(
                volunteer=volunteer,
                date=date(2026, 10, 5),
                start_time=time(9, 0),
            ).exists()
        )

        self.assertTrue(
            VolunteerAvailability.objects.filter(
                volunteer=volunteer,
                date=date(2026, 10, 7),
                start_time=time(13, 0),
            ).exists()
        )

        self.assertEqual(
            VolunteerAvailability.objects.filter(
                volunteer=volunteer
            ).count(),
            1,
        )

    # VT16 - Verifies that a Volunteer can schedule a visit with an assigned Senior.
    def test_volunteer_can_schedule_visit_with_assigned_senior(self):
        user, volunteer = self.create_volunteer_user()
        senior_user, senior = self.create_senior()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
        )

        availability = VolunteerAvailability.objects.create(
            volunteer=volunteer,
            date=date(2026, 10, 20),
            start_time=time(10, 0),
            end_time=time(12, 0),
        )

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "volunteer_schedule_visit",
                args=[senior.pk],
            ),
            {
                "availability_id": availability.pk,
                "visit_type": "home_visit",
                "visit_purpose": "regular_check_in",
                "support_types": ["emotional"],
                "other_support_details": "",
                "estimated_duration": "60",
                "notes": "Regular welfare visit.",
            },
        )

        self.assertRedirects(
            response,
            reverse("volunteer_schedule"),
        )

        self.assertEqual(
            ScheduledVisit.objects.count(),
            1,
        )

        visit = ScheduledVisit.objects.first()

        self.assertEqual(
            visit.assignment,
            assignment,
        )

        self.assertEqual(
            visit.visit_date,
            date(2026, 10, 20),
        )

        self.assertEqual(
            visit.start_time,
            time(10, 0),
        )

        self.assertEqual(
            visit.end_time,
            time(11, 0),
        )

        self.assertEqual(
            visit.status,
            "scheduled",
        )

        self.assertEqual(
            visit.support_types,
            ["emotional"],
        )

    # VT17 - Verifies that a visit cannot exceed the selected availability slot.
    def test_visit_cannot_exceed_availability_slot(self):
        user, volunteer = self.create_volunteer_user()
        senior_user, senior = self.create_senior()

        SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
        )

        availability = VolunteerAvailability.objects.create(
            volunteer=volunteer,
            date=date(2026, 10, 20),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "volunteer_schedule_visit",
                args=[senior.pk],
            ),
            {
                "availability_id": availability.pk,
                "visit_type": "home_visit",
                "visit_purpose": "regular_check_in",
                "support_types": ["emotional"],
                "other_support_details": "",
                "estimated_duration": "120",
                "notes": "",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "volunteer_schedule_visit",
                args=[senior.pk],
            ),
        )

        self.assertEqual(
            ScheduledVisit.objects.count(),
            0,
        )

    # VT18 - Verifies that a Volunteer cannot schedule a conflicting visit.
    def test_volunteer_cannot_schedule_conflicting_visit(self):
        user, volunteer = self.create_volunteer_user()
        senior_user, senior = self.create_senior()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
        )

        availability = VolunteerAvailability.objects.create(
            volunteer=volunteer,
            date=date(2026, 10, 20),
            start_time=time(10, 0),
            end_time=time(12, 0),
        )

        ScheduledVisit.objects.create(
            assignment=assignment,
            visit_date=date(2026, 10, 20),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status="scheduled",
        )

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "volunteer_schedule_visit",
                args=[senior.pk],
            ),
            {
                "availability_id": availability.pk,
                "visit_type": "home_visit",
                "visit_purpose": "regular_check_in",
                "support_types": ["emotional"],
                "other_support_details": "",
                "estimated_duration": "60",
                "notes": "",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "volunteer_schedule_visit",
                args=[senior.pk],
            ),
        )

        self.assertEqual(
            ScheduledVisit.objects.count(),
            1,
        )

    # VT19 - Verifies that a Volunteer can submit a report for a scheduled visit.
    def test_volunteer_can_submit_visit_report(self):
        user, volunteer = self.create_volunteer_user()
        senior_user, senior = self.create_senior()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
        )

        visit = ScheduledVisit.objects.create(
            assignment=assignment,
            visit_date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status="scheduled",
        )

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse(
                "submit_visit_report",
                args=[visit.pk],
            ),
            {
                "wellbeing_status": "good",
                "assistance_provided": "Completed regular check-in.",
                "observations": "Senior appeared well.",
                "concerns": "",
                "follow_up_required": "",
                "follow_up_notes": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("volunteer_check_in_reports"),
        )

        self.assertEqual(
            VisitReport.objects.count(),
            1,
        )

        report = VisitReport.objects.first()

        self.assertEqual(
            report.visit,
            visit,
        )

        self.assertEqual(
            report.wellbeing_status,
            "good",
        )

        visit.refresh_from_db()

        self.assertEqual(
            visit.status,
            "completed",
        )

    # VT20 - Verifies that a visit report cannot be submitted before the visit date.
    def test_report_cannot_be_submitted_before_visit_date(self):
        user, volunteer = self.create_volunteer_user()
        senior_user, senior = self.create_senior()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
        )

        visit = ScheduledVisit.objects.create(
            assignment=assignment,
            visit_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status="scheduled",
        )

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "submit_visit_report",
                args=[visit.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("volunteer_check_in_reports"),
        )

        self.assertEqual(
            VisitReport.objects.count(),
            0,
        )

        visit.refresh_from_db()

        self.assertEqual(
            visit.status,
            "scheduled",
        )

    # VT21 - Verifies that a visit report cannot be submitted for a cancelled visit.
    def test_report_cannot_be_submitted_for_cancelled_visit(self):
        user, volunteer = self.create_volunteer_user()
        senior_user, senior = self.create_senior()

        assignment = SeniorVolunteerAssignment.objects.create(
            senior=senior,
            volunteer=volunteer,
        )

        visit = ScheduledVisit.objects.create(
            assignment=assignment,
            visit_date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status="cancelled",
        )

        self.client.login(
            username=user.username,
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "submit_visit_report",
                args=[visit.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("volunteer_check_in_reports"),
        )

        self.assertEqual(
            VisitReport.objects.count(),
            0,
        )

        visit.refresh_from_db()

        self.assertEqual(
            visit.status,
            "cancelled",
        )
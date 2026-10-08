from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from ideas.models import Category, ProjectIdea

from .models import Booking, BookingMember, BookingStatus
from .services import approve_booking, cancel_booking, create_booking, reject_booking


def make_idea(**kwargs):
    category, _ = Category.objects.get_or_create(name="عام")
    defaults = {
        "title": "فكرة اختبار",
        "description": "وصف",
        "category": category,
        "max_members": 4,
    }
    defaults.update(kwargs)
    return ProjectIdea.objects.create(**defaults)


def make_user(username, role=User.ROLE_STUDENT):
    return User.objects.create_user(username=username, password="pw", role=role)


class BookingServiceTests(TestCase):
    def setUp(self):
        self.idea = make_idea()
        self.student = make_user("s1")
        self.supervisor = make_user("sup", User.ROLE_SUPERVISOR)
        self.idea.supervisor = self.supervisor
        self.idea.save(update_fields=["supervisor"])

    def test_create_booking_with_members(self):
        booking = create_booking(
            idea=self.idea,
            student=self.student,
            note="",
            members=[
                {"full_name": "عضو اثنان", "university_number": "111"},
                {"full_name": "عضو ثلاث", "university_number": "222"},
            ],
        )
        self.assertEqual(booking.status, BookingStatus.PENDING)
        self.assertEqual(booking.team_size, 3)
        self.assertEqual(booking.members.count(), 2)

    def test_empty_member_rows_ignored(self):
        booking = create_booking(
            idea=self.idea,
            student=self.student,
            note="",
            members=[{"full_name": "  ", "university_number": "x"}],
        )
        self.assertEqual(booking.members.count(), 0)
        self.assertEqual(booking.team_size, 1)

    def test_one_active_booking_per_idea(self):
        create_booking(idea=self.idea, student=self.student, note="", members=[])
        other = make_user("s2")
        with self.assertRaises(ValidationError):
            create_booking(idea=self.idea, student=other, note="", members=[])

    def test_one_active_booking_per_student(self):
        create_booking(idea=self.idea, student=self.student, note="", members=[])
        other = make_idea(title="فكرة أخرى")
        with self.assertRaises(ValidationError):
            create_booking(idea=other, student=self.student, note="", members=[])

    def test_team_size_limit(self):
        members = [{"full_name": f"عضو {i}"} for i in range(5)]
        with self.assertRaises(ValidationError):
            create_booking(
                idea=self.idea, student=self.student, note="", members=members
            )

    def test_cannot_book_closed_idea(self):
        self.idea.status = ProjectIdea.STATUS_CLOSED
        self.idea.save(update_fields=["status"])
        with self.assertRaises(ValidationError):
            create_booking(idea=self.idea, student=self.student, note="", members=[])

    def test_approve_locks_idea(self):
        booking = create_booking(idea=self.idea, student=self.student, note="", members=[])
        approve_booking(booking=booking, user=self.supervisor)
        booking.refresh_from_db()
        self.idea.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.APPROVED)
        self.assertEqual(self.idea.status, ProjectIdea.STATUS_BOOKED)

    def test_approve_by_unrelated_user_denied(self):
        from django.core.exceptions import PermissionDenied

        booking = create_booking(idea=self.idea, student=self.student, note="", members=[])
        stranger = make_user("stranger", User.ROLE_SUPERVISOR)
        with self.assertRaises(PermissionDenied):
            approve_booking(booking=booking, user=stranger)

    def test_reject_frees_idea(self):
        booking = create_booking(idea=self.idea, student=self.student, note="", members=[])
        reject_booking(booking=booking, user=self.supervisor)
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.REJECTED)
        # يمكن لطالب آخر الحجز بعدها
        other = make_user("s2")
        booking2 = create_booking(idea=self.idea, student=other, note="", members=[])
        self.assertEqual(booking2.status, BookingStatus.PENDING)

    def test_cancel_approved_reopens_idea(self):
        booking = create_booking(idea=self.idea, student=self.student, note="", members=[])
        approve_booking(booking=booking, user=self.supervisor)
        cancel_booking(booking=booking, user=self.student)
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.status, ProjectIdea.STATUS_APPROVED)

    def test_student_cannot_cancel_others_booking(self):
        from django.core.exceptions import PermissionDenied

        booking = create_booking(idea=self.idea, student=self.student, note="", members=[])
        other = make_user("s2")
        with self.assertRaises(PermissionDenied):
            cancel_booking(booking=booking, user=other)


class BookingViewTests(TestCase):
    def setUp(self):
        self.idea = make_idea()
        self.student = make_user("s1")
        self.supervisor = make_user("sup", User.ROLE_SUPERVISOR)
        self.idea.supervisor = self.supervisor
        self.idea.save(update_fields=["supervisor"])

    def test_booking_via_post(self):
        self.client.login(username="s1", password="pw")
        response = self.client.post(
            reverse("ideas:book", args=[self.idea.slug]),
            {
                "member_name": ["أحمد علي", ""],
                "member_number": ["333", ""],
            },
        )
        self.assertRedirects(response, reverse("bookings:mine"))
        booking = Booking.objects.get(student=self.student)
        self.assertEqual(booking.members.count(), 1)
        self.assertEqual(booking.members.first().full_name, "أحمد علي")

    def test_anonymous_cannot_book(self):
        response = self.client.post(reverse("ideas:book", args=[self.idea.slug]), {})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_supervisor_dashboard_requires_role(self):
        self.client.login(username="s1", password="pw")
        response = self.client.get(reverse("supervisor:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_supervisor_dashboard_shows_pending(self):
        create_booking(idea=self.idea, student=self.student, note="", members=[])
        self.client.login(username="sup", password="pw")
        response = self.client.get(reverse("supervisor:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "فكرة اختبار")

    def test_approve_via_view(self):
        booking = create_booking(idea=self.idea, student=self.student, note="", members=[])
        self.client.login(username="sup", password="pw")
        response = self.client.post(
            reverse("supervisor:decide", args=[booking.pk, "approve"])
        )
        self.assertEqual(response.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.APPROVED)

    def test_my_bookings_page(self):
        create_booking(idea=self.idea, student=self.student, note="", members=[])
        self.client.login(username="s1", password="pw")
        response = self.client.get(reverse("bookings:mine"))
        self.assertContains(response, "فكرة اختبار")

    def test_db_constraint_blocks_double_booking(self):
        """اختبار القيد في قاعدة البيانات نفسه (لا الخدمة فقط)."""
        create_booking(idea=self.idea, student=self.student, note="", members=[])
        other = make_user("s2")
        with self.assertRaises(Exception):
            Booking.objects.create(idea=self.idea, student=other)

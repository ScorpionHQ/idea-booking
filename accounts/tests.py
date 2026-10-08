from django.test import TestCase
from django.urls import reverse

from .models import User


class RegisterTests(TestCase):
    def test_register_creates_student_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "ali",
                "first_name": "علي حسن",
                "university_number": "20231111",
                "email": "ali@example.com",
                "password1": "StrongPass!2026",
                "password2": "StrongPass!2026",
            },
        )
        self.assertRedirects(response, reverse("ideas:list"))
        user = User.objects.get(username="ali")
        self.assertEqual(user.role, User.ROLE_STUDENT)
        self.assertEqual(user.university_number, "20231111")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_login_page_renders(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تسجيل الدخول")

    def test_logout(self):
        User.objects.create_user(username="x", password="pw", role=User.ROLE_STUDENT)
        self.client.login(username="x", password="pw")
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)

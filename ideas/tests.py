from django.test import TestCase
from django.urls import reverse

from .models import Category, ProjectIdea


class IdeaTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="ويب")
        self.idea = ProjectIdea.objects.create(
            title="نظام حجز",
            description="وصف تجريبي",
            category=self.category,
            max_members=4,
        )

    def test_slug_auto_generated(self):
        self.assertTrue(self.idea.slug)

    def test_list_page(self):
        response = self.client.get(reverse("ideas:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "نظام حجز")

    def test_detail_page(self):
        response = self.client.get(reverse("ideas:detail", args=[self.idea.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "وصف تجريبي")

    def test_search_filter(self):
        response = self.client.get(reverse("ideas:list"), {"q": "حجز"})
        self.assertContains(response, "نظام حجز")
        response = self.client.get(reverse("ideas:list"), {"q": "لايوجد"})
        self.assertNotContains(response, "نظام حجز")

    def test_add_idea_requires_supervisor(self):
        from accounts.models import User

        student = User.objects.create_user(
            username="s1", password="pw", role=User.ROLE_STUDENT
        )
        self.client.login(username="s1", password="pw")
        response = self.client.get(reverse("ideas:add"))
        self.assertEqual(response.status_code, 403)

    def test_supervisor_can_add_idea(self):
        from accounts.models import User

        sup = User.objects.create_user(
            username="sup", password="pw", role=User.ROLE_SUPERVISOR
        )
        self.client.login(username="sup", password="pw")
        response = self.client.post(
            reverse("ideas:add"),
            {
                "title": "فكرة جديدة",
                "description": "وصف",
                "category": self.category.pk,
                "max_members": 3,
                "status": "approved",
            },
        )
        self.assertEqual(response.status_code, 302)
        idea = ProjectIdea.objects.get(title="فكرة جديدة")
        self.assertEqual(idea.supervisor, sup)

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from MyApp.models import Profile, Role, Request


class UnhousedDashboardTests(TestCase):
    def setUp(self):
        self.unhoused_role, _ = Role.objects.get_or_create(name="unhoused")
        self.volunteer_role, _ = Role.objects.get_or_create(name="volunteer")

        self.unhoused_user = User.objects.create_user(
            username="unhoused@example.com",
            email="unhoused@example.com",
            password="SecurePass123!",
            first_name="Test",
            last_name="Unhoused",
        )
        self.unhoused_profile, _ = Profile.objects.get_or_create(user=self.unhoused_user)
        self.unhoused_profile.role = self.unhoused_role
        self.unhoused_profile.display_username = "unhoused_user"
        self.unhoused_profile.save()

        self.volunteer_user = User.objects.create_user(
            username="volunteer@example.com",
            email="volunteer@example.com",
            password="SecurePass123!",
            first_name="Test",
            last_name="Volunteer",
        )
        self.volunteer_profile, _ = Profile.objects.get_or_create(user=self.volunteer_user)
        self.volunteer_profile.role = self.volunteer_role
        self.volunteer_profile.display_username = "volunteer_user"
        self.volunteer_profile.save()

    def login_as_unhoused(self):
        self.client.login(username="unhoused@example.com", password="SecurePass123!")

    def make_request(self, status, category=Request.CATEGORY_FOOD, claimed=False):
        return Request.objects.create(
            requester=self.unhoused_profile,
            claimed_by=self.volunteer_profile if claimed else None,
            claimed_at=timezone.now() if claimed else None,
            title=f"{status} request",
            category=category,
            city="Milwaukee",
            status=status,
        )

    # Access control

    def test_requires_login(self):
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_volunteer_is_redirected_to_home(self):
        self.client.login(username="volunteer@example.com", password="SecurePass123!")
        resp = self.client.get(reverse("unhoused"))
        self.assertRedirects(resp, reverse("home"))

    def test_unhoused_user_can_access_dashboard(self):
        self.login_as_unhoused()
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "unhoused_dash.html")

    # Request display

    def test_open_requests_appear(self):
        self.login_as_unhoused()
        self.make_request(Request.STATUS_OPEN)
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.context["open_requests"].count(), 1)

    def test_claimed_requests_appear_as_processing(self):
        self.login_as_unhoused()
        self.make_request(Request.STATUS_CLAIMED, claimed=True)
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.context["processing_requests"].count(), 1)

    def test_fulfilled_requests_appear_as_completed(self):
        self.login_as_unhoused()
        self.make_request(Request.STATUS_FULFILLED, claimed=True)
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.context["completed_requests"].count(), 1)

    def test_cancelled_requests_are_hidden(self):
        self.login_as_unhoused()
        self.make_request(Request.STATUS_CANCELLED)
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.context["open_requests"].count(), 0)
        self.assertEqual(resp.context["processing_requests"].count(), 0)
        self.assertEqual(resp.context["completed_requests"].count(), 0)

    def test_renders_with_no_requests(self):
        self.login_as_unhoused()
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "unhoused_dash.html")
        self.assertEqual(resp.context["open_requests"].count(), 0)
        self.assertEqual(resp.context["processing_requests"].count(), 0)
        self.assertEqual(resp.context["completed_requests"].count(), 0)

    # Filtering

    def test_only_shows_own_requests(self):
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="SecurePass123!",
        )
        other_profile, _ = Profile.objects.get_or_create(user=other_user)
        other_profile.role = self.unhoused_role
        other_profile.display_username = "other_user"
        other_profile.save()

        self.make_request(Request.STATUS_OPEN)
        Request.objects.create(
            requester=other_profile,
            title="Someone else's request",
            category=Request.CATEGORY_CLOTHING,
            city="Milwaukee",
            status=Request.STATUS_OPEN,
        )

        self.login_as_unhoused()
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.context["open_requests"].count(), 1)
        self.assertEqual(resp.context["open_requests"][0].requester, self.unhoused_profile)

    def test_all_statuses_are_separated(self):
        self.login_as_unhoused()
        self.make_request(Request.STATUS_OPEN)
        self.make_request(Request.STATUS_CLAIMED, claimed=True)
        self.make_request(Request.STATUS_FULFILLED, claimed=True)
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.context["open_requests"].count(), 1)
        self.assertEqual(resp.context["processing_requests"].count(), 1)
        self.assertEqual(resp.context["completed_requests"].count(), 1)

    # Ordering

    def test_open_requests_newest_first(self):
        self.login_as_unhoused()
        req1 = self.make_request(Request.STATUS_OPEN)
        Request.objects.filter(pk=req1.pk).update(created_at=timezone.now() - timedelta(seconds=5))
        req2 = self.make_request(Request.STATUS_OPEN, category=Request.CATEGORY_CLOTHING)
        resp = self.client.get(reverse("unhoused"))
        open_requests = list(resp.context["open_requests"])
        self.assertEqual(open_requests[0].id, req2.id)
        self.assertEqual(open_requests[1].id, req1.id)

    def test_processing_requests_most_recently_claimed_first(self):
        self.login_as_unhoused()
        req1 = Request.objects.create(
            requester=self.unhoused_profile,
            claimed_by=self.volunteer_profile,
            claimed_at=timezone.now() - timedelta(seconds=5),
            title="Claimed earlier",
            category=Request.CATEGORY_FOOD,
            city="Milwaukee",
            status=Request.STATUS_CLAIMED,
        )
        req2 = Request.objects.create(
            requester=self.unhoused_profile,
            claimed_by=self.volunteer_profile,
            claimed_at=timezone.now(),
            title="Claimed later",
            category=Request.CATEGORY_CLOTHING,
            city="Milwaukee",
            status=Request.STATUS_CLAIMED,
        )
        resp = self.client.get(reverse("unhoused"))
        processing_requests = list(resp.context["processing_requests"])
        self.assertEqual(len(processing_requests), 2)
        self.assertEqual(processing_requests[0].id, req2.id)
        self.assertEqual(processing_requests[1].id, req1.id)

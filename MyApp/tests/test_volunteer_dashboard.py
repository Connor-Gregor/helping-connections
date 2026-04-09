from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from MyApp.models import Profile, Role, Request, Offer


class VolunteerDashboardTests(TestCase):
    def setUp(self):
        self.volunteer_role, _ = Role.objects.get_or_create(name="volunteer")
        self.unhoused_role, _ = Role.objects.get_or_create(name="unhoused")

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

    def login_as_volunteer(self):
        self.client.login(username="volunteer@example.com", password="SecurePass123!")

    def make_claimed_request(self, category=Request.CATEGORY_FOOD, claimed_at=None):
        return Request.objects.create(
            requester=self.unhoused_profile,
            claimed_by=self.volunteer_profile,
            claimed_at=claimed_at or timezone.now(),
            title="Test request",
            category=category,
            city="Milwaukee",
            status=Request.STATUS_CLAIMED,
        )

    def make_claimed_offer(self, category=Offer.CATEGORY_FOOD, claimed_at=None):
        return Offer.objects.create(
            offered_by=self.volunteer_profile,
            claimed_by=self.unhoused_profile,
            claimed_at=claimed_at or timezone.now(),
            title="Test offer",
            category=category,
            city="Milwaukee",
            status=Offer.STATUS_CLAIMED,
        )

    # Access control

    def test_requires_login(self):
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_unhoused_user_is_redirected_to_home(self):
        self.client.login(username="unhoused@example.com", password="SecurePass123!")
        resp = self.client.get(reverse("volunteer"))
        self.assertRedirects(resp, reverse("home"))

    def test_volunteer_user_can_access_dashboard(self):
        self.login_as_volunteer()
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "volunteer_dash.html")

    # Renders with no data

    def test_renders_with_no_activity(self):
        self.login_as_volunteer()
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "volunteer_dash.html")
        self.assertEqual(len(resp.context["accepted_requests"]), 0)
        self.assertEqual(len(resp.context["accepted_offers"]), 0)
        self.assertEqual(resp.context["fulfilled_requests_count"], 0)

    # Accepted requests

    def test_claimed_request_appears_in_accepted_requests(self):
        self.login_as_volunteer()
        self.make_claimed_request()
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(len(resp.context["accepted_requests"]), 1)

    def test_fulfilled_and_cancelled_requests_do_not_appear_in_accepted_requests(self):
        self.login_as_volunteer()
        for status in [Request.STATUS_FULFILLED, Request.STATUS_CANCELLED]:
            Request.objects.create(
                requester=self.unhoused_profile,
                claimed_by=self.volunteer_profile,
                claimed_at=timezone.now(),
                title=f"{status} request",
                category=Request.CATEGORY_FOOD,
                city="Milwaukee",
                status=status,
            )
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(len(resp.context["accepted_requests"]), 0)

    def test_open_request_does_not_appear_in_accepted_requests(self):
        self.login_as_volunteer()
        Request.objects.create(
            requester=self.unhoused_profile,
            title="Open request",
            category=Request.CATEGORY_FOOD,
            city="Milwaukee",
            status=Request.STATUS_OPEN,
        )
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(len(resp.context["accepted_requests"]), 0)

    def test_accepted_requests_only_shows_this_volunteers_claims(self):
        other_volunteer_user = User.objects.create_user(
            username="other_vol@example.com",
            email="other_vol@example.com",
            password="SecurePass123!",
        )
        other_profile, _ = Profile.objects.get_or_create(user=other_volunteer_user)
        other_profile.role = self.volunteer_role
        other_profile.display_username = "other_vol"
        other_profile.save()

        self.make_claimed_request()
        Request.objects.create(
            requester=self.unhoused_profile,
            claimed_by=other_profile,
            claimed_at=timezone.now(),
            title="Other volunteer's claim",
            category=Request.CATEGORY_CLOTHING,
            city="Milwaukee",
            status=Request.STATUS_CLAIMED,
        )

        self.login_as_volunteer()
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(len(resp.context["accepted_requests"]), 1)
        self.assertEqual(resp.context["accepted_requests"][0].claimed_by, self.volunteer_profile)

    def test_accepted_requests_ordered_most_recently_claimed_first(self):
        self.login_as_volunteer()
        req1 = self.make_claimed_request(
            category=Request.CATEGORY_FOOD,
            claimed_at=timezone.now() - timedelta(seconds=5),
        )
        req2 = self.make_claimed_request(
            category=Request.CATEGORY_CLOTHING,
            claimed_at=timezone.now(),
        )
        resp = self.client.get(reverse("volunteer"))
        accepted = list(resp.context["accepted_requests"])
        self.assertEqual(accepted[0].id, req2.id)
        self.assertEqual(accepted[1].id, req1.id)

    # Accepted offers

    def test_claimed_offer_appears_in_accepted_offers(self):
        self.login_as_volunteer()
        self.make_claimed_offer()
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(len(resp.context["accepted_offers"]), 1)

    def test_fulfilled_and_cancelled_offers_do_not_appear_in_accepted_offers(self):
        self.login_as_volunteer()
        for status in [Offer.STATUS_FULFILLED, Offer.STATUS_CANCELLED]:
            Offer.objects.create(
                offered_by=self.volunteer_profile,
                claimed_by=self.unhoused_profile,
                claimed_at=timezone.now(),
                title=f"{status} offer",
                category=Offer.CATEGORY_FOOD,
                city="Milwaukee",
                status=status,
            )
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(len(resp.context["accepted_offers"]), 0)

    def test_open_offer_does_not_appear_in_accepted_offers(self):
        self.login_as_volunteer()
        Offer.objects.create(
            offered_by=self.volunteer_profile,
            title="Open offer",
            category=Offer.CATEGORY_FOOD,
            city="Milwaukee",
            status=Offer.STATUS_OPEN,
        )
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(len(resp.context["accepted_offers"]), 0)

    def test_accepted_offers_only_shows_this_volunteers_offers(self):
        other_volunteer_user = User.objects.create_user(
            username="other_vol2@example.com",
            email="other_vol2@example.com",
            password="SecurePass123!",
        )
        other_profile, _ = Profile.objects.get_or_create(user=other_volunteer_user)
        other_profile.role = self.volunteer_role
        other_profile.display_username = "other_vol2"
        other_profile.save()

        self.make_claimed_offer()
        Offer.objects.create(
            offered_by=other_profile,
            claimed_by=self.unhoused_profile,
            claimed_at=timezone.now(),
            title="Other volunteer's offer",
            category=Offer.CATEGORY_CLOTHING,
            city="Milwaukee",
            status=Offer.STATUS_CLAIMED,
        )

        self.login_as_volunteer()
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(len(resp.context["accepted_offers"]), 1)
        self.assertEqual(resp.context["accepted_offers"][0].offered_by, self.volunteer_profile)

    def test_accepted_offers_ordered_most_recently_claimed_first(self):
        self.login_as_volunteer()
        offer1 = self.make_claimed_offer(
            category=Offer.CATEGORY_FOOD,
            claimed_at=timezone.now() - timedelta(seconds=5),
        )
        offer2 = self.make_claimed_offer(
            category=Offer.CATEGORY_CLOTHING,
            claimed_at=timezone.now(),
        )
        resp = self.client.get(reverse("volunteer"))
        accepted = list(resp.context["accepted_offers"])
        self.assertEqual(accepted[0].id, offer2.id)
        self.assertEqual(accepted[1].id, offer1.id)

    def test_volunteer_own_claimed_request_excluded_from_accepted_requests(self):
        # If a volunteer is also the requester, it should not appear in their accepted list
        Request.objects.create(
            requester=self.volunteer_profile,
            claimed_by=self.volunteer_profile,
            claimed_at=timezone.now(),
            title="Self request",
            category=Request.CATEGORY_FOOD,
            city="Milwaukee",
            status=Request.STATUS_CLAIMED,
        )
        self.login_as_volunteer()
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(len(resp.context["accepted_requests"]), 0)

    def test_volunteer_own_fulfilled_request_excluded_from_count(self):
        # Self-fulfilled requests should not count toward the fulfilled total
        Request.objects.create(
            requester=self.volunteer_profile,
            claimed_by=self.volunteer_profile,
            claimed_at=timezone.now(),
            title="Self fulfilled request",
            category=Request.CATEGORY_FOOD,
            city="Milwaukee",
            status=Request.STATUS_FULFILLED,
        )
        self.login_as_volunteer()
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(resp.context["fulfilled_requests_count"], 0)

    # Fulfilled requests count

    def test_fulfilled_requests_count_is_correct(self):
        self.login_as_volunteer()
        Request.objects.create(
            requester=self.unhoused_profile,
            claimed_by=self.volunteer_profile,
            claimed_at=timezone.now(),
            title="Fulfilled request",
            category=Request.CATEGORY_FOOD,
            city="Milwaukee",
            status=Request.STATUS_FULFILLED,
        )
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(resp.context["fulfilled_requests_count"], 1)

    def test_fulfilled_count_does_not_include_other_volunteers(self):
        other_volunteer_user = User.objects.create_user(
            username="other_vol3@example.com",
            email="other_vol3@example.com",
            password="SecurePass123!",
        )
        other_profile, _ = Profile.objects.get_or_create(user=other_volunteer_user)
        other_profile.role = self.volunteer_role
        other_profile.display_username = "other_vol3"
        other_profile.save()

        Request.objects.create(
            requester=self.unhoused_profile,
            claimed_by=other_profile,
            claimed_at=timezone.now(),
            title="Other volunteer fulfilled",
            category=Request.CATEGORY_FOOD,
            city="Milwaukee",
            status=Request.STATUS_FULFILLED,
        )

        self.login_as_volunteer()
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(resp.context["fulfilled_requests_count"], 0)

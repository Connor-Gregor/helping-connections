from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from MyApp.models import Profile, Role, Request


class RequestWorkflowTests(TestCase):
    def setUp(self):
        self.unhoused_role, _ = Role.objects.get_or_create(name="unhoused")
        self.volunteer_role, _ = Role.objects.get_or_create(name="volunteer")

        self.unhoused_user = User.objects.create_user(
            username="unhoused@example.com",
            email="unhoused@example.com",
            password="SecurePass123!",
        )
        self.unhoused_profile, _ = Profile.objects.get_or_create(user=self.unhoused_user)
        self.unhoused_profile.role = self.unhoused_role
        self.unhoused_profile.display_username = "unhoused_user"
        self.unhoused_profile.save()

        self.volunteer_user = User.objects.create_user(
            username="volunteer@example.com",
            email="volunteer@example.com",
            password="SecurePass123!",
        )
        self.volunteer_profile, _ = Profile.objects.get_or_create(user=self.volunteer_user)
        self.volunteer_profile.role = self.volunteer_role
        self.volunteer_profile.display_username = "volunteer_user"
        self.volunteer_profile.save()

        self.request_item = Request.objects.create(
            requester=self.unhoused_profile,
            title="Need food",
            description="Need meals",
            category=Request.CATEGORY_FOOD,
            city="Milwaukee",
            location_details="Shelter",
            status=Request.STATUS_OPEN,
        )

    #Claiming offer sets status, claimer, and timestamp
    def test_claim_request_sets_status_claimer_and_claimed_at(self):
        self.client.login(username="volunteer@example.com", password="SecurePass123!")

        resp = self.client.post(reverse("claim_request", args=[self.request_item.id]))

        self.assertEqual(resp.status_code, 302)
        self.request_item.refresh_from_db()
        self.assertEqual(self.request_item.status, Request.STATUS_CLAIMED)
        self.assertEqual(self.request_item.claimed_by, self.volunteer_profile)
        self.assertIsNotNone(self.request_item.claimed_at)

    #Cannot claim already claimed offer
    def test_claim_request_blocks_already_claimed_request(self):
        self.request_item.status = Request.STATUS_CLAIMED
        self.request_item.claimed_by = self.volunteer_profile
        self.request_item.claimed_at = timezone.now()
        self.request_item.save()

        self.client.login(username="volunteer@example.com", password="SecurePass123!")
        resp = self.client.post(reverse("claim_request", args=[self.request_item.id]))

        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("volunteer_requests"))

    @patch("MyApp.views.send_system_dm")
    def test_update_claimed_request_reopens_and_sends_dm(self, mock_send_dm):
        self.request_item.status = Request.STATUS_CLAIMED
        self.request_item.claimed_by = self.volunteer_profile
        self.request_item.claimed_at = timezone.now()
        self.request_item.save()

        self.client.login(username="unhoused@example.com", password="SecurePass123!")
        resp = self.client.post(reverse("update_request", args=[self.request_item.id]), {
            "title": "Need more food",
            "description": "Updated request",
            "category": Request.CATEGORY_FOOD,
            "city": "Milwaukee",
            "location_details": "Library",
        })

        self.assertEqual(resp.status_code, 302)
        self.request_item.refresh_from_db()
        self.assertEqual(self.request_item.status, Request.STATUS_OPEN)
        self.assertIsNone(self.request_item.claimed_by)
        self.assertIsNone(self.request_item.claimed_at)
        mock_send_dm.assert_called_once()

    #Deleting claimed offer sends notifications
    @patch("MyApp.views.send_system_dm")
    def test_delete_claimed_request_sends_dm(self, mock_send_dm):
        self.request_item.status = Request.STATUS_CLAIMED
        self.request_item.claimed_by = self.volunteer_profile
        self.request_item.claimed_at = timezone.now()
        self.request_item.save()

        self.client.login(username="unhoused@example.com", password="SecurePass123!")
        resp = self.client.post(reverse("delete_request", args=[self.request_item.id]))

        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Request.objects.filter(id=self.request_item.id).exists())
        mock_send_dm.assert_called_once()

    #Verifying offer marks it fulfilled and sends notification
    @patch("MyApp.views.send_system_dm")
    def test_verify_request_marks_fulfilled_and_sends_dm(self, mock_send_dm):
        self.request_item.status = Request.STATUS_CLAIMED
        self.request_item.claimed_by = self.volunteer_profile
        self.request_item.claimed_at = timezone.now()
        self.request_item.save()

        self.client.login(username="unhoused@example.com", password="SecurePass123!")
        resp = self.client.post(reverse("verify_request", args=[self.request_item.id]))

        self.assertEqual(resp.status_code, 302)
        self.request_item.refresh_from_db()
        self.assertEqual(self.request_item.status, Request.STATUS_FULFILLED)
        mock_send_dm.assert_called_once()

    @patch("MyApp.views.send_system_dm")
    def test_withdraw_claimed_request_reopens_and_sends_dm(self, mock_send_dm):
        self.request_item.status = Request.STATUS_CLAIMED
        self.request_item.claimed_by = self.volunteer_profile
        self.request_item.claimed_at = timezone.now()
        self.request_item.save()

        self.client.login(username="volunteer@example.com", password="SecurePass123!")
        resp = self.client.post(reverse("withdraw_claimed_request", args=[self.request_item.id]))

        self.assertEqual(resp.status_code, 302)
        self.request_item.refresh_from_db()
        self.assertEqual(self.request_item.status, Request.STATUS_OPEN)
        self.assertIsNone(self.request_item.claimed_by)
        self.assertIsNone(self.request_item.claimed_at)
        mock_send_dm.assert_called_once()
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from MyApp.models import Profile, Role


class LoginAndDashboardTests(TestCase):

    def setUp(self):
        # Create roles
        self.unhoused_role = Role.objects.create(name="unhoused")
        self.volunteer_role = Role.objects.create(name="volunteer")

        # Create users
        self.unhoused_user = User.objects.create_user(
            username="unhoused@test.com",
            password="password123"
        )

        self.volunteer_user = User.objects.create_user(
            username="volunteer@test.com",
            password="password123"
        )

        # Create profiles
        Profile.objects.create(user=self.unhoused_user, role=self.unhoused_role)
        Profile.objects.create(user=self.volunteer_user, role=self.volunteer_role)

    # -----------------------
    # LOGIN TESTS
    # -----------------------

    def test_login_success(self):
        response = self.client.post(reverse("login"), {
            "email": "unhoused@test.com",
            "password": "password123"
        })

        # should redirect after login
        self.assertEqual(response.status_code, 302)

    def test_login_failure(self):
        response = self.client.post(reverse("login"), {
            "email": "wrong@test.com",
            "password": "wrongpass"
        })

        # stays on page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email or password")

    # -----------------------
    # DASHBOARD TESTS
    # -----------------------

    def test_unhoused_dashboard_access(self):
        self.client.login(username="unhoused@test.com", password="password123")

        response = self.client.get(reverse("unhoused"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unhoused Dashboard")

    def test_volunteer_dashboard_access(self):
        self.client.login(username="volunteer@test.com", password="password123")

        response = self.client.get(reverse("volunteer"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Volunteer Dashboard")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("unhoused"))

        # should redirect to login
        self.assertEqual(response.status_code, 302)
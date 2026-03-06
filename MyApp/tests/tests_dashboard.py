from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from MyApp.models import Profile, Role

class DashBoardAndLoginTests(TestCase):
    def CreateUserWithRole(self, email, password, role_name=None, display_username=None):
        user = User.objects.create_user(username = email, email = email, password = password)
        
        role = None
        if role_name is not None:
            role, _ = Role.objects.get_or_create(name=role_name)
            
        if display_username is None:
            display_username = f"user_{user.id}"
            
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.display_username = display_username
        profile.phone_number = ""
        profile.save()
        return user

    """Dashboard tests"""    
    def test_home_dashboard_public_renders(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home.html")
        
    def test_home_dashboard_renders_logged_in(self):
        user = self.CreateUserWithRole("dash@example.com", "pw123", role_name = "volunteer")
        self.client.login(username = "dash@example.com", password = "pw123")
        
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home.html")
        
        
    """Login page tests"""
    def test_login_get_renders_template(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "login.html")

    def test_login_post_invalid_credentials_shows_error(self):
        resp = self.client.post(reverse("login"), {"email": "nope@example.com", "password": "wrong"})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "login.html")
        self.assertContains(resp, "Invalid email or password.")

    def test_login_volunteer_redirects_to_volunteer_dashboard(self):
        self.CreateUserWithRole("vol@example.com", "pw123", role_name="volunteer")

        resp = self.client.post(reverse("login"), {"email": "vol@example.com", "password": "pw123"})
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("volunteer"))

        follow = self.client.get(reverse("volunteer"))
        self.assertEqual(follow.wsgi_request.user.is_authenticated, True)

    def test_login_unhoused_redirects_to_unhoused_dashboard(self):
        self.CreateUserWithRole("unhoused@example.com", "pw123", role_name="unhoused")

        resp = self.client.post(reverse("login"), {"email": "unhoused@example.com", "password": "pw123"})
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("unhoused"))

    def test_login_user_with_no_role_redirects_home(self):
        self.CreateUserWithRole("norole@example.com", "pw123", role_name=None)

        resp = self.client.post(reverse("login"), {"email": "norole@example.com", "password": "pw123"})
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("home"))

    def test_login_sets_session_expiry_about_300_seconds(self):
        self.CreateUserWithRole("expiry@example.com", "pw123", role_name="volunteer")

        self.client.post(reverse("login"), {"email": "expiry@example.com", "password": "pw123"})
        expiry_age = self.client.session.get_expiry_age()
        self.assertTrue(1 <= expiry_age <= 300)
        
    """Role Dashboard access"""
    def test_volunteer_dashboard_requires_login(self):
        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_unhoused_dashboard_requires_login(self):
        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_volunteer_dashboard_denies_unhoused_user(self):
        self.CreateUserWithRole("u@example.com", "pw123", role_name="unhoused")
        self.client.login(username="u@example.com", password="pw123")

        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("home"))

    def test_unhoused_dashboard_denies_volunteer_user(self):
        self.CreateUserWithRole("v@example.com", "pw123", role_name="volunteer")
        self.client.login(username="v@example.com", password="pw123")

        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("home"))

    def test_volunteer_dashboard_allows_volunteer_user(self):
        self.CreateUserWithRole("v2@example.com", "pw123", role_name="volunteer")
        self.client.login(username="v2@example.com", password="pw123")

        resp = self.client.get(reverse("volunteer"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "volunteer.html")

    def test_unhoused_dashboard_allows_unhoused_user(self):
        self.CreateUserWithRole("u2@example.com", "pw123", role_name="unhoused")
        self.client.login(username="u2@example.com", password="pw123")

        resp = self.client.get(reverse("unhoused"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "unhoused_dash.html")

    """Dashboard redirect tests"""
    def test_dashboard_redirect_requires_login(self):
        resp = self.client.get(reverse("dashboard_redirect"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_dashboard_redirect_sends_volunteer_to_volunteer(self):
        self.CreateUserWithRole("vdash@example.com", "pw123", role_name="volunteer")
        self.client.login(username="vdash@example.com", password="pw123")

        resp = self.client.get(reverse("dashboard_redirect"))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("volunteer"))

    def test_dashboard_redirect_sends_unhoused_to_unhoused(self):
        self.CreateUserWithRole("udash@example.com", "pw123", role_name="unhoused")
        self.client.login(username="udash@example.com", password="pw123")

        resp = self.client.get(reverse("dashboard_redirect"))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("unhoused"))

    def test_dashboard_redirect_sends_user_with_no_role_to_home(self):
        self.CreateUserWithRole("ndash@example.com", "pw123", role_name=None)
        self.client.login(username="ndash@example.com", password="pw123")

        resp = self.client.get(reverse("dashboard_redirect"))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("home"))
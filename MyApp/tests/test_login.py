from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from MyApp.models import Profile, Role


class LoginSecurityTests(TestCase):
    def setUp(self):
        self.email = "testuser@example.com"
        self.password = "S3cureP@ssw0rd"
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            first_name="Test",
            last_name="User",
        )
        # Ensure a Profile exists (views access user.profile); a post_save signal
        # may already create it, so use get_or_create.
        self.profile, _ = Profile.objects.get_or_create(user=self.user)
        if not self.profile.display_username:
            self.profile.display_username = "testuser"
            self.profile.save()
        self.client = Client()

    def test_get_login_page_shows_form_fields(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)
        self.assertContains(resp, 'name="email"')
        self.assertContains(resp, 'name="password"')

    def test_successful_login_sets_session_and_expiry_and_redirects(self):
        resp = self.client.post(reverse("login"), {"email": self.email, "password": self.password})
        # Should redirect on success
        self.assertEqual(resp.status_code, 302)

        session = self.client.session
        self.assertIn("_auth_user_id", session)
        # View sets explicit expiry of 300 seconds
        self.assertEqual(session.get_expiry_age(), 300)

    def test_invalid_credentials_show_non_field_error(self):
        resp = self.client.post(reverse("login"), {"email": self.email, "password": "wrong"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        form = resp.context.get("form")
        self.assertIsNotNone(form)
        non_field = form.non_field_errors()
        self.assertTrue(non_field)
        self.assertIn("Invalid email or password.", non_field)

    def test_logout_clears_auth_session(self):
        # Log in using the test client helper, then logout endpoint
        self.client.login(username=self.email, password=self.password)
        resp = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_csrf_required_for_post(self):
        client_csrf = Client(enforce_csrf_checks=True)
        # POST without fetching CSRF token should be rejected
        resp = client_csrf.post(reverse("login"), {"email": self.email, "password": self.password})
        self.assertEqual(resp.status_code, 403)

        # Now fetch login page to get csrf cookie and token, then post with token
        get_resp = client_csrf.get(reverse("login"))
        csrftoken = get_resp.cookies.get("csrftoken").value
        post_data = {"email": self.email, "password": self.password, "csrfmiddlewaretoken": csrftoken}
        resp2 = client_csrf.post(reverse("login"), post_data, follow=True)
        self.assertEqual(resp2.status_code, 200)
        # After successful login the client should be authenticated
        self.assertIn("_auth_user_id", client_csrf.session)

    def test_next_parameter_does_not_open_redirect(self):
        # The login view does not honor external next, so an external next param should not redirect externally
        malicious_next = "https://evil.example.com/"
        resp = self.client.post(reverse("login") + f"?next={malicious_next}", {"email": self.email, "password": self.password})
        self.assertEqual(resp.status_code, 302)
        location = resp["Location"]
        # Expect internal redirect (home) not external host
        self.assertTrue(location.startswith("/"))

    def test_many_failed_attempts_do_not_crash(self):
        # Simulate multiple failed logins to ensure no server error and consistent error messaging
        for _ in range(12):
            resp = self.client.post(reverse("login"), {"email": self.email, "password": "badpw"})
            self.assertEqual(resp.status_code, 200)
            # form should contain non-field error
            form = resp.context.get("form")
            self.assertIsNotNone(form)
            self.assertTrue(form.non_field_errors())

    def test_password_is_hashed_and_check_password_works(self):
        u = User.objects.get(pk=self.user.pk)
        # Raw password should not be stored
        self.assertNotEqual(u.password, self.password)
        self.assertTrue(u.check_password(self.password))

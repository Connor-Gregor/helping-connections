from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from MyApp.models import Profile, Role, Request


class CreateRequestTests(TestCase):

    """set up user"""
    def setUp(self):
        self.url = reverse("create_request")

        # create unhoused user
        self.user = User.objects.create_user(
            username="test@user.com",
            password="password123"
        )
        role = Role.objects.create(name="unhoused")
        self.profile = Profile.objects.get(user=self.user)
        self.profile.role = role
        self.profile.save()

    """redirected if not logged in"""
    def test_create_request_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    """blocks non-unhoused users"""
    def test_create_request_wrong_role_redirect(self):
        volunteer_role = Role.objects.create(name="volunteer")
        self.profile.role = volunteer_role
        self.profile.save()

        self.client.login(username="test@user.com", password="password123")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    """page loads correctly"""
    def test_create_request_get_renders_page(self):
        self.client.login(username="test@user.com", password="password123")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_request.html")

    """creates reqeust on valid form"""
    def test_create_request_valid_post(self):
        self.client.login(username="test@user.com", password="password123")

        data = {
            "title": "Need food",
            "description": "Need meals",
            "category": "food",
            "city": "Milwaukee",
            "location_details": "Shelter"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Request.objects.count(), 1)

    """no request created on invalid form"""
    def test_create_request_invalid_post(self):
        self.client.login(username="test@user.com", password="password123")

        data = {
            "title": "",  # invalid
            "description": "Need meals",
            "category": "food",
            "city": "Milwaukee",
            "location_details": "Shelter"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Request.objects.count(), 0)
        
    #Request linked to correct requester
    def test_create_request_sets_requester_correctly(self):
        self.client.login(username="test@user.com", password="password123")

        data = {
            "title": "Need blankets",
            "description": "Need blankets for cold weather",
            "category": "blankets",
            "city": "Milwaukee",
            "location_details": "Near shelter",
        }

        self.client.post(self.url, data)

        req = Request.objects.get()
        self.assertEqual(req.requester, self.profile)

    #Request created with OPEN status
    def test_create_request_sets_status_open(self):
        self.client.login(username="test@user.com", password="password123")

        data = {
            "title": "Need hygiene kit",
            "description": "Soap and toothpaste",
            "category": "hygiene",
            "city": "Milwaukee",
            "location_details": "Library area",
        }

        self.client.post(self.url, data)

        req = Request.objects.get()
        self.assertEqual(req.status, Request.STATUS_OPEN)    
    
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from MyApp.models import Profile, Role, Offer
from django.core.files.uploadedfile import SimpleUploadedFile
from MyApp.models import Offer, OfferImage

class CreateOfferTests(TestCase):

    """set up"""
    def setUp(self):
        self.url = reverse("create_offer")

        # create volunteer user
        self.user = User.objects.create_user(
            username="test@user.com",
            password="password123"
        )
        role = Role.objects.create(name="volunteer")
        self.profile = Profile.objects.get(user=self.user)
        self.profile.role = role
        self.profile.save()

    """redirect if not logged in"""
    def test_create_offer_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    """blocks non-volunteer users"""
    def test_create_offer_wrong_role_redirect(self):
        unhoused_role = Role.objects.create(name="unhoused")
        self.profile.role = unhoused_role
        self.profile.save()

        self.client.login(username="test@user.com", password="password123")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    """page loads correctly"""
    def test_create_offer_get_renders_page(self):
        self.client.login(username="test@user.com", password="password123")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_offer.html")

    """create offer on valid form"""
    def test_create_offer_valid_post(self):
        self.client.login(username="test@user.com", password="password123")

        data = {
            "title": "Offer food",
            "description": "Free meals",
            "category": "food",
            "city": "Milwaukee",
            "location_details": "Downtown"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Offer.objects.count(), 1)

    """no offer created on invalid form"""
    def test_create_offer_invalid_post(self):
        self.client.login(username="test@user.com", password="password123")

        data = {
            "title": "",  # invalid
            "description": "Free meals",
            "category": "food",
            "city": "Milwaukee",
            "location_details": "Downtown"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Offer.objects.count(), 0)

    """create offer with image"""
    def test_create_offer_with_image(self):
        self.client.login(username="test@user.com", password="password123")

        image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )

        data = {
            "title": "Offer food",
            "description": "Free meals",
            "category": "food",
            "city": "Milwaukee",
            "location_details": "Downtown",
        }

        response = self.client.post(
            self.url,
            data,
            files={"offer_images": image}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Offer.objects.count(), 1)
        
    #Offer linked to correct volunteer
    def test_create_offer_sets_offered_by_correctly(self):
        self.client.login(username="test@user.com", password="password123")

        data = {
            "title": "Offer clothes",
            "description": "Jackets and socks",
            "category": "clothing",
            "city": "Milwaukee",
            "location_details": "Community center",
        }

        self.client.post(self.url, data)

        offer = Offer.objects.get()
        self.assertEqual(offer.offered_by, self.profile)

    #Offer created with OPEN status
    def test_create_offer_sets_status_open(self):
        self.client.login(username="test@user.com", password="password123")

        data = {
            "title": "Offer bedding",
            "description": "Blankets available",
            "category": "blankets",
            "city": "Milwaukee",
            "location_details": "Church parking lot",
        }

        self.client.post(self.url, data)

        offer = Offer.objects.get()
        self.assertEqual(offer.status, Offer.STATUS_OPEN)
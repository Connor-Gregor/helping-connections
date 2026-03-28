from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class RegisterPageTests(TestCase):
    
    def setUp(self):
        self.url = reverse('register')
        self.valid_user_data = {
            'email': 'test@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'volunteer',

            'display_username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '1234567890',

            'address_line1': '123 Main St',
            'address_line2': '',
            'city': 'Milwaukee',
            'state': 'WI',
            'zip_code': '53202',
        }
        
    """Register page loads"""
    def test_register_page_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
    """Register page template"""
    def test_register_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'register.html')

    """Registration form"""
    def test_register_page_contains_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, '<form')

    """Valid data entered"""
    def test_register_valid_user_creation(self):
        response = self.client.post(self.url, self.valid_user_data)

        self.assertEqual(response.status_code, 302)

        self.assertTrue(User.objects.filter(username='test@example.com').exists())

    """Password mismatch does not create user"""
    def test_register_password_mismatch(self):
        invalid_data = self.valid_user_data.copy()
        invalid_data['password2'] = 'WrongPass123!'

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 200)

        self.assertFalse(User.objects.filter(username='test@example.com').exists())

        self.assertContains(response, "password")

    """Duplicate username rejected"""
    def test_register_duplicate_username(self):
        User.objects.create_user(
            username='test@example.com',
            email='existing@example.com',
            password='Password123!'
        )

        response = self.client.post(self.url, self.valid_user_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "username")

    """Missing fields"""
    def test_register_missing_fields(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='').exists())
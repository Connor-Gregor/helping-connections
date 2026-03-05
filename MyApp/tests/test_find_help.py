# MyApp/tests/test_find_help.py

from django.test import TestCase
from django.urls import reverse

class FindHelpPageTests(TestCase):
    def setUp(self):
        self.url = reverse('find_help')
        self.response = self.client.get(self.url)

    def test_find_help_page_status_code(self):
        """Test that the Find Help page loads successfully."""
        self.assertEqual(self.response.status_code, 200)

    def test_find_help_uses_correct_template(self):
        """Test that the correct template is used."""
        self.assertTemplateUsed(self.response, 'find_help.html')

    def test_main_headings_present(self):
        """Test that all key section headings appear on the page."""
        headings = [
            "Shelter & Housing",
            "Food Assistance",
            "Medical",
            "Employment",
            "Legal Aid",
            "Hygiene"
        ]
        for heading in headings:
            self.assertContains(self.response, heading)

    def test_back_to_dashboard_link_exists(self):
        """Test that 'Back to Dashboard' link exists and points correctly."""
        dashboard_url = reverse('dashboard_redirect')
        self.assertContains(self.response, f'href="{dashboard_url}"')

    def test_external_links_present(self):
        """Test that some of the key external links are present."""
        links = [
            "https://county.milwaukee.gov/EN/DHHS/Housing/Housing-First",
            "https://www.guesthouseofmilwaukee.org/",
            "https://www.hungertaskforce.org/",
            "https://svdpmilw.org/meal-program/",
            "https://dcf.wisconsin.gov/w2/tmj",
            "https://legalaction.org/",
            "https://www.findhelp.org/health/personal-hygiene--milwaukee-wi"
        ]
        for link in links:
            self.assertContains(self.response, f'href="{link}"')

    def test_links_open_in_new_tab(self):
        """Test that external links have target='_blank'."""
        external_link_targets = self.response.content.decode()
        self.assertIn('target="_blank"', external_link_targets)
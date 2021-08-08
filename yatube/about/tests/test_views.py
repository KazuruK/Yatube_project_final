from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_page_accessible_by_name(self):
        reverse_url = [
            reverse('about:author'),
            reverse('about:tech')
        ]

        for url_name in reverse_url:
            with self.subTest(url_name=url_name):
                response = self.guest_client.get(url_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_page_uses_correct_template(self):
        reverse_to_template = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

        for url_name, template in reverse_to_template.items():
            with self.subTest(url_name=url_name):
                response = self.guest_client.get(url_name)
                self.assertTemplateUsed(response, template)

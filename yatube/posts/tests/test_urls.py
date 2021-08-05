from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        user = User.objects.create_user(
            'test_admin',
            'admin@admin.com',
            'admin'
        )
        user.last_name = 'adminov'
        user.save()
        cls.user = user
        user2 = User.objects.create_user(
            'test_authorized_user',
            'authorized@user.ru',
            'user'
        )
        user2.last_name = 'usered'
        user2.save()
        cls.user2 = user2

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskURLTests.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(TaskURLTests.user2)

    def test_guest_urls(self):
        non_login_required_urls = [
            '/',
            f'/group/{TaskURLTests.group.slug}/',
            f'/{TaskURLTests.user.username}/',
            f'/{TaskURLTests.user.username}/{TaskURLTests.post.id}/'
        ]
        for adress in non_login_required_urls:
            with self.subTest(adress=adress):
                self.assertEqual(
                    self.guest_client.get(adress).status_code,
                    HTTPStatus.OK
                )

    def test_redirect_urls(self):

        login_required_urls = {
            '/group/': '/auth/login/?next=/group/',
            '/new/': '/auth/login/?next=/new/'
        }

        for adress, redirect in login_required_urls.items():
            with self.subTest(adress=adress):
                self.assertRedirects(
                    self.guest_client.get(adress, follow=True),
                    redirect
                )

        redirect_urls = {
            f'/{TaskURLTests.user.username}/follow/':
                f'/{TaskURLTests.user.username}/',
            f'/{TaskURLTests.user.username}/unfollow/':
                f'/{TaskURLTests.user.username}/',
        }

        for adress, redirect in redirect_urls.items():
            with self.subTest(adress=adress):
                self.assertRedirects(
                    self.authorized_client2.get(adress, follow=True),
                    redirect
                )

    def test_authorized_user(self):

        all_urls = [
            '/',
            '/follow/',
            '/new/',
            '/group/',
            f'/group/{TaskURLTests.group.slug}/',
            f'/{TaskURLTests.user.username}/',
            f'/{TaskURLTests.user.username}/{TaskURLTests.post.id}/'
        ]

        for adress in all_urls:
            with self.subTest(adress=adress):
                self.assertEqual(
                    self.authorized_client.get(adress).status_code,
                    HTTPStatus.OK
                )

    def test_access_edit(self):
        adress = f'/{TaskURLTests.user.username}/{TaskURLTests.post.id}/edit/'
        response_guest = self.guest_client.get(adress, follow=True)
        response_user = self.authorized_client2.get(adress, follow=True)
        response_author = self.authorized_client.get(adress)

        self.assertRedirects(
            response_guest,
            f'/auth/login/?next=/{TaskURLTests.user.username}/'
            f'{TaskURLTests.post.id}/edit/'
        )
        self.assertRedirects(
            response_user,
            f'/{TaskURLTests.user.username}/{TaskURLTests.post.id}/'
        )
        self.assertEqual(
            response_author.status_code,
            HTTPStatus.OK
        )

    def test_page_not_found(self):
        self.assertEqual(
            self.authorized_client.get('/404/').status_code,
            HTTPStatus.NOT_FOUND
        )

    def test_urls_uses_correct_template(self):

        templates_url_names = {
            '/': 'posts/index.html',
            '/new/': 'posts/new_post.html',
            '/group/': 'posts/groups.html',
            f'/group/{TaskURLTests.group.slug}/': 'posts/group.html',
            f'/{TaskURLTests.user.username}/': 'posts/profile.html',
            f'/{TaskURLTests.user.username}/'
            f'{TaskURLTests.post.id}/': 'posts/post.html',
            f'/{TaskURLTests.user.username}/'
            f'{TaskURLTests.post.id}/edit/': 'posts/new_post.html',
            '/404/': 'misc/404.html'
        }

        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

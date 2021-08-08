from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

GROUP_SLUG = 'test'
USERNAME = 'test_admin'
USERNAME_FOLLOW = 'test_authorized_user'
REDIRECT = reverse('login') + '?next='
INDEX_URL = reverse('posts:index')
ALL_GROUPS_URL = reverse('posts:all_groups')
GROUP_URL = reverse('posts:group_posts', args=[GROUP_SLUG])
NEW_POST_URL = reverse('posts:new_post')
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME])
PAGE_NOT_FOUND_URL = PROFILE_UNFOLLOW_URL + '404/'


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(
            USERNAME,
            'admin@admin.com',
            'admin'
        )
        user.last_name = 'adminov'
        user.save()
        cls.user = user
        user2 = User.objects.create_user(
            USERNAME_FOLLOW,
            'authorized@user.ru',
            'user'
        )
        user2.last_name = 'usered'
        user2.save()
        cls.user2 = user2
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(user2)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=user
        )
        cls.POST_URL = reverse('posts:post', args=[USERNAME, cls.post.id])
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[USERNAME, cls.post.id]
        )
        cls.POST_COMMENT_URL = reverse(
            'posts:add_comment',
            args=[USERNAME, cls.post.id]
        )

    def test_urls(self):
        url_client_status = [
            [INDEX_URL, self.guest_client, HTTPStatus.OK],
            [ALL_GROUPS_URL, self.guest_client, HTTPStatus.FOUND],
            [ALL_GROUPS_URL, self.authorized_client, HTTPStatus.OK],
            [GROUP_URL, self.guest_client, HTTPStatus.OK],
            [NEW_POST_URL, self.guest_client, HTTPStatus.FOUND],
            [NEW_POST_URL, self.authorized_client, HTTPStatus.OK],
            [FOLLOW_URL, self.guest_client, HTTPStatus.FOUND],
            [FOLLOW_URL, self.authorized_client, HTTPStatus.OK],
            [PROFILE_URL, self.guest_client, HTTPStatus.OK],
            [PROFILE_FOLLOW_URL, self.guest_client, HTTPStatus.FOUND],
            [PROFILE_FOLLOW_URL, self.authorized_client2, HTTPStatus.FOUND],
            [PROFILE_UNFOLLOW_URL, self.guest_client, HTTPStatus.FOUND],
            [PROFILE_UNFOLLOW_URL, self.authorized_client2, HTTPStatus.FOUND],
            [self.POST_URL, self.guest_client, HTTPStatus.OK],
            [self.POST_EDIT_URL, self.guest_client, HTTPStatus.FOUND],
            [self.POST_EDIT_URL, self.authorized_client, HTTPStatus.OK],
            [self.POST_EDIT_URL, self.authorized_client2, HTTPStatus.FOUND],
            [self.POST_COMMENT_URL, self.guest_client, HTTPStatus.FOUND],
            [self.POST_COMMENT_URL, self.authorized_client, HTTPStatus.FOUND],
            [PAGE_NOT_FOUND_URL, self.guest_client, HTTPStatus.NOT_FOUND],
            [PAGE_NOT_FOUND_URL, self.authorized_client, HTTPStatus.NOT_FOUND],
        ]
        for url, client, status_code in url_client_status:
            with self.subTest(url=url, client=client, status=status_code):
                self.assertEqual(
                    client.get(url).status_code,
                    status_code
                )

    def test_redirect(self):
        url_client_redirect = [
            [ALL_GROUPS_URL, self.guest_client, REDIRECT + ALL_GROUPS_URL],
            [NEW_POST_URL, self.guest_client, REDIRECT + NEW_POST_URL],
            [FOLLOW_URL, self.guest_client, REDIRECT + FOLLOW_URL],
            [
                PROFILE_FOLLOW_URL,
                self.guest_client,
                REDIRECT + PROFILE_FOLLOW_URL
            ],
            [PROFILE_FOLLOW_URL, self.authorized_client2, PROFILE_URL],
            [
                PROFILE_UNFOLLOW_URL,
                self.guest_client,
                REDIRECT + PROFILE_UNFOLLOW_URL
            ],
            [PROFILE_UNFOLLOW_URL, self.authorized_client2, PROFILE_URL],
            [
                self.POST_EDIT_URL,
                self.guest_client,
                REDIRECT + self.POST_EDIT_URL
            ],
            [self.POST_EDIT_URL, self.authorized_client2, self.POST_URL],
            [
                self.POST_COMMENT_URL,
                self.guest_client,
                REDIRECT + self.POST_COMMENT_URL
            ],
            [self.POST_COMMENT_URL, self.authorized_client, self.POST_URL],
        ]
        for url, client, redirect in url_client_redirect:
            with self.subTest(url=url, client=client, redirect=redirect):
                self.assertRedirects(
                    client.get(url, follow=True),
                    redirect
                )

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            INDEX_URL: 'posts/index.html',
            NEW_POST_URL: 'posts/new_post.html',
            ALL_GROUPS_URL: 'posts/groups.html',
            GROUP_URL: 'posts/group.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_URL: 'posts/post.html',
            self.POST_EDIT_URL: 'posts/new_post.html',
            PAGE_NOT_FOUND_URL: 'misc/404.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress, template=template):
                self.assertTemplateUsed(
                    self.authorized_client.get(adress),
                    template
                )

from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

GROUP_SLUG = 'test'
USERNAME = 'test_admin'
USERNAME_FOLLOW = 'test_authorized_user'
REDIRECT = '/auth/login/?next='
PAGE_NOT_FOUND = '404/'
INDEX_URL = reverse('posts:index')
ALL_GROUPS_URL = reverse('posts:all_groups')
GROUP_URL = reverse('posts:group_posts', kwargs={'slug': GROUP_SLUG})
NEW_POST_URL = reverse('posts:new_post')
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
PROFILE_FOLLOW_URL = reverse(
    'posts:profile_follow',
    kwargs={'username': USERNAME}
)
PROFILE_UNFOLLOW_URL = reverse(
    'posts:profile_unfollow',
    kwargs={'username': USERNAME}
)


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
        cls.POST_URL = reverse(
            'posts:post',
            kwargs={
                'username': USERNAME,
                'post_id': TaskURLTests.post.id
            }
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={
                'username': USERNAME,
                'post_id': TaskURLTests.post.id
            }
        )
        cls.POST_COMMENT_URL = reverse(
            'posts:add_comment',
            kwargs={
                'username': USERNAME,
                'post_id': TaskURLTests.post.id
            }
        )

    def test_urls(self):
        url_client_status = [
            [INDEX_URL, self.guest_client, HTTPStatus.OK],
            [INDEX_URL, self.authorized_client, HTTPStatus.OK],
            [ALL_GROUPS_URL, self.guest_client, HTTPStatus.FOUND],
            [ALL_GROUPS_URL, self.authorized_client, HTTPStatus.OK],
            [GROUP_URL, self.guest_client, HTTPStatus.OK],
            [GROUP_URL, self.authorized_client, HTTPStatus.OK],
            [NEW_POST_URL, self.guest_client, HTTPStatus.FOUND],
            [NEW_POST_URL, self.authorized_client, HTTPStatus.OK],
            [FOLLOW_URL, self.guest_client, HTTPStatus.FOUND],
            [FOLLOW_URL, self.authorized_client, HTTPStatus.OK],
            [PROFILE_URL, self.guest_client, HTTPStatus.OK],
            [PROFILE_URL, self.authorized_client, HTTPStatus.OK],
            [PROFILE_FOLLOW_URL, self.guest_client, HTTPStatus.FOUND],
            [PROFILE_FOLLOW_URL, self.authorized_client2, HTTPStatus.FOUND],
            [PROFILE_UNFOLLOW_URL, self.guest_client, HTTPStatus.FOUND],
            [PROFILE_UNFOLLOW_URL, self.authorized_client2, HTTPStatus.FOUND],
            [self.POST_URL, self.guest_client, HTTPStatus.OK],
            [self.POST_URL, self.authorized_client, HTTPStatus.OK],
            [self.POST_EDIT_URL, self.guest_client, HTTPStatus.FOUND],
            [self.POST_EDIT_URL, self.authorized_client, HTTPStatus.OK],
            [self.POST_EDIT_URL, self.authorized_client2, HTTPStatus.FOUND],
            [self.POST_COMMENT_URL, self.guest_client, HTTPStatus.FOUND],
            [self.POST_COMMENT_URL, self.authorized_client, HTTPStatus.FOUND],
            [
                self.POST_COMMENT_URL + PAGE_NOT_FOUND,
                self.guest_client,
                HTTPStatus.NOT_FOUND
            ],
            [
                self.POST_COMMENT_URL + PAGE_NOT_FOUND,
                self.authorized_client,
                HTTPStatus.NOT_FOUND
            ],
        ]
        for test in url_client_status:
            with self.subTest(test=test):
                self.assertEqual(
                    test[1].get(test[0]).status_code,
                    test[2]
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
        for test in url_client_redirect:
            with self.subTest(test=test):
                self.assertRedirects(
                    test[1].get(test[0], follow=True),
                    test[2]
                )

    def test_page_not_found(self):
        self.assertEqual(
            self.authorized_client.get('/404/').status_code,
            HTTPStatus.NOT_FOUND
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
            self.POST_EDIT_URL + PAGE_NOT_FOUND: 'misc/404.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                self.assertTemplateUsed(
                    self.authorized_client.get(adress),
                    template
                )
import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import FollowAuthor, Group, Post, User

TEST_DIR = 'test_data'
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
GROUP_SLUG = 'test'
EMPTY_GROUP_SLUG = 'empty_test'
USERNAME = 'test_admin'
USERNAME_FOLLOW_TEST1 = 'test_authorized_user1'
USERNAME_FOLLOW_TEST2 = 'test_authorized_user2'
REDIRECT = reverse('login') + '?next='
INDEX_URL = reverse('posts:index')
ALL_GROUPS_URL = reverse('posts:all_groups')
GROUP_URL = reverse('posts:group_posts', args=[GROUP_SLUG])
EMPTY_GROUP_URL = reverse('posts:group_posts', args=[EMPTY_GROUP_SLUG])
NEW_POST_URL = reverse('posts:new_post')
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
PROFILE_FOLLOW_URL = reverse(
    'posts:profile_follow',
    args=[USERNAME_FOLLOW_TEST1]
)
PROFILE_UNFOLLOW_URL = reverse(
    'posts:profile_unfollow',
    args=[USERNAME_FOLLOW_TEST2]
)


@override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        user = User.objects.create_user(
            USERNAME,
            'admin@admin.com',
            'admin'
        )
        user.last_name = 'adminov'
        user.save()
        user2 = User.objects.create_user(
            'client',
            'client@client.com',
            'client'
        )
        user2.last_name = 'client'
        user2.save()
        cls.user = user
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(user2)
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание группы'
        )
        cls.empty_group = Group.objects.create(
            title='Пустая тестовая группа',
            slug=EMPTY_GROUP_SLUG,
            description='Тестовое описание пустой группы'
        )
        cls.post = Post.objects.create(
            text='В тестовой группе содержится тестовый пост',
            group=cls.group,
            author=user,
            image=cls.image
        )
        cls.follow = FollowAuthor.objects.create(
            user=user2,
            author=user
        )
        cls.POST_URL = reverse(
            'posts:post',
            args=[USERNAME, cls.post.id]
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.delete('index_page')

    def test_correct_post_in_context(self):
        list_urls_post_in_context = [
            [INDEX_URL, 'page'],
            [FOLLOW_URL, 'page'],
            [GROUP_URL, 'page'],
            [PROFILE_URL, 'page'],
            [self.POST_URL, 'post']
        ]
        for url, key in list_urls_post_in_context:
            with self.subTest(url=url, key=key):
                response = self.authorized_client.get(url)
                if key == 'page':
                    self.assertEqual(len(response.context[key]), 1)
                    post = response.context[key][0]
                else:
                    post = response.context[key]
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.image, self.post.image)
        response_empty_group = self.authorized_client.get(EMPTY_GROUP_URL)
        self.assertNotContains(response_empty_group, self.post)

    def test_correct_user_in_context(self):
        list_urls_user_in_context = [PROFILE_URL, self.POST_URL]
        for url in list_urls_user_in_context:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context['author'], self.user)

    def test_correct_group_in_context(self):
        list_urls_user_in_context = [GROUP_URL, ALL_GROUPS_URL]
        for url in list_urls_user_in_context:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if url == ALL_GROUPS_URL:
                    for group_item in response.context['page']:
                        if group_item.id == self.group.id:
                            group = group_item
                    self.assertEqual(group, self.group)
                else:
                    group = response.context['group']
                self.assertEqual(group.title, self.group.title)
                self.assertEqual(group.slug, self.group.slug)
                self.assertEqual(group.description, self.group.description)


class PaginatorViewsTest(TestCase):
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
        cls.guest_client = Client()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание группы'
        )
        Post.objects.bulk_create(
            (Post(
                text='Текст',
                author=user,
                group=cls.group
            ) for _ in range(settings.PAGINATOR_POSTS_PER_PAGE + 1)),
            batch_size=10)

    def setUp(self):
        cache.delete('index_page')

    def test_paginator(self):
        url_to_posts_count = [INDEX_URL, GROUP_URL, PROFILE_URL]
        for url in url_to_posts_count:
            with self.subTest(url=url):
                first_page_response = self.guest_client.get(url)
                self.assertEqual(
                    len(first_page_response.context['page']),
                    settings.PAGINATOR_POSTS_PER_PAGE
                )
                second_page_response = self.guest_client.get(url + '?page=2')
                self.assertEqual(
                    len(second_page_response.context['page']),
                    (second_page_response.context['page'].paginator.count
                     - settings.PAGINATOR_POSTS_PER_PAGE)
                )


class TaskCacheTests(TestCase):
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
        cls.guest_client = Client()
        cls.post = Post.objects.create(
            text='В тестовой группе содержится тестовый пост',
            author=user,
        )

    def setUp(self):
        cache.delete('index_page')

    def test_cache(self):
        response = self.guest_client.get(INDEX_URL)
        Post.objects.create(text='text', author=self.user)
        response2 = self.guest_client.get(INDEX_URL)
        self.assertEqual(response2.content, response.content)
        cache.delete('index_page')
        response3 = self.guest_client.get(INDEX_URL)
        self.assertTrue(response3.content != response2.content)


class TaskFollowTests(TestCase):
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
            USERNAME_FOLLOW_TEST1,
            'authorized@user1.ru',
            'user1'
        )
        user2.last_name = 'usered'
        user2.save()
        cls.user2 = user2
        user3 = User.objects.create_user(
            USERNAME_FOLLOW_TEST2,
            'authorized@user2.ru',
            'user2'
        )
        user3.last_name = 'usered'
        user3.save()
        cls.user3 = user3
        cls.authorized_client = Client()
        cls.authorized_client.force_login(user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(user2)
        cls.authorized_client3 = Client()
        cls.authorized_client3.force_login(user3)
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=user
        )
        cls.post = Post.objects.create(
            text='Тестовый пост от второго юзера',
            author=user2
        )
        cls.follow = FollowAuthor.objects.create(
            user=user2,
            author=user3
        )

    def test_follow(self):
        self.authorized_client.get(PROFILE_FOLLOW_URL)
        self.assertTrue(
            FollowAuthor.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_unfollow(self):
        self.authorized_client2.get(PROFILE_UNFOLLOW_URL)
        self.assertTrue(
            not FollowAuthor.objects.filter(
                user=self.user2,
                author=self.user3
            ).exists()
        )

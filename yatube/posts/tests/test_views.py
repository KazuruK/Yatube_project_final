import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

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
REDIRECT = '/auth/login/?next='
INDEX_URL = reverse('posts:index')
ALL_GROUPS_URL = reverse('posts:all_groups')
GROUP_URL = reverse('posts:group_posts', kwargs={'slug': GROUP_SLUG})
EMPTY_GROUP_URL = reverse(
    'posts:group_posts',
    kwargs={'slug': EMPTY_GROUP_SLUG}
)
NEW_POST_URL = reverse('posts:new_post')
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
PROFILE_FOLLOW_URL = reverse(
    'posts:profile_follow',
    kwargs={'username': USERNAME_FOLLOW_TEST1}
)
PROFILE_UNFOLLOW_URL = reverse(
    'posts:profile_unfollow',
    kwargs={'username': USERNAME_FOLLOW_TEST2}
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
        cls.post_in_group = Post.objects.create(
            text='В тестовой группе содержится тестовый пост',
            group=TaskPagesTests.group,
            author=user,
            image=TaskPagesTests.image
        )
        cls.follow = Follow.objects.create(
            user=user2,
            author=user
        )
        cls.POST_URL = reverse(
            'posts:post',
            kwargs={
                'username': USERNAME,
                'post_id': TaskPagesTests.post_in_group.id
            }
        )


    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.delete('index_page')

    def test_correct_post_in_context(self):
        values = {
            'group': self.post_in_group.group,
            'text': self.post_in_group.text,
            'pub_date': self.post_in_group.pub_date,
            'author': self.post_in_group.author,
            'image': 'posts/small.gif'
        }
        list_urls_post_in_context = [
            [INDEX_URL, 'page'],
            [FOLLOW_URL, 'page'],
            [GROUP_URL, 'page'],
            [PROFILE_URL, 'page'],
            [self.POST_URL, 'post']
        ]
        for test in list_urls_post_in_context:
            with self.subTest(test=test):
                response = self.authorized_client.get(test[0])
                if test[1] == 'page':
                    context_post = response.context[test[1]][0]
                else:
                    context_post = response.context[test[1]]
                self.assertEqual(context_post.group, values['group'])
                self.assertEqual(context_post.text, values['text'])
                self.assertEqual(context_post.pub_date, values['pub_date'])
                self.assertEqual(context_post.author, values['author'])
                self.assertEqual(context_post.image, values['image'])
        response_empty_group = self.authorized_client.get(EMPTY_GROUP_URL)
        self.assertTrue(
            self.post_in_group not in response_empty_group.context['page']
        )


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
                group=PaginatorViewsTest.group
            ) for _ in range(11)),
            batch_size=10)

    def setUp(self):
        cache.delete('index_page')

    def test_paginator(self):
        reverse_to_posts_count = [INDEX_URL, GROUP_URL, PROFILE_URL]
        for reverse_name in reverse_to_posts_count:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page']),
                    settings.PAGINATOR_POSTS_PER_PAGE
                )
        for reverse_name in reverse_to_posts_count:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page']),
                    1)


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
        cls.follow = Follow.objects.create(
            user=user2,
            author=user3
        )

    def test_follow(self):
        self.authorized_client.get(PROFILE_FOLLOW_URL)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_unfollow(self):
        self.authorized_client2.get(PROFILE_UNFOLLOW_URL)
        self.assertTrue(
            not Follow.objects.filter(
                user=self.user2,
                author=self.user3
            ).exists()
        )

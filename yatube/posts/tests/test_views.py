import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
TEST_DIR = 'test_data'


@override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        user = User.objects.create_user(
            'test_admin',
            'admin@admin.com',
            'admin'
        )
        user.last_name = 'adminov'
        user.save()
        cls.user = user

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание группы'
        )
        cls.empty_group = Group.objects.create(
            title='Пустая тестовая группа',
            slug='empty_test',
            description='Тестовое описание пустой группы'
        )

        cls.post_in_group = Post.objects.create(
            text='В тестовой группе содержится тестовый пост',
            group=TaskPagesTests.group,
            author=user,
            image=TaskPagesTests.image
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.delete('index_page')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskPagesTests.user)

    def test_pages_use_correct_templates(self):
        template_to_reverse = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:new_post'): 'posts/new_post.html',
            reverse('posts:all_groups'): 'posts/groups.html',
            reverse(
                'posts:group_posts',
                kwargs={
                    'slug': TaskPagesTests.group.slug
                }
            ): 'posts/group.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': TaskPagesTests.user.username
                }
            ): 'posts/profile.html',
            reverse(
                'posts:post',
                kwargs={
                    'username': TaskPagesTests.user.username,
                    'post_id': TaskPagesTests.post_in_group.id,
                }
            ): 'posts/post.html',
            reverse(
                'posts:post_edit',
                kwargs={
                    'username': TaskPagesTests.user.username,
                    'post_id': TaskPagesTests.post_in_group.id
                }
            ): 'posts/new_post.html',
        }
        for reverse_name, template in template_to_reverse.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_and_post_group_work_correct(self):
        response_group_post_in_index = self.authorized_client.get(
            reverse('posts:index')
        )
        first_object = response_group_post_in_index.context['page'][0]
        self.assertEqual(
            first_object.text,
            TaskPagesTests.post_in_group.text
        )
        self.assertEqual(
            first_object.author,
            TaskPagesTests.user
        )

        response_group = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={
                    'slug': TaskPagesTests.group.slug
                }
            )
        )
        post_object = response_group.context['page'][0]
        self.assertEqual(
            post_object.text,
            TaskPagesTests.post_in_group.text
        )
        self.assertEqual(
            post_object.author,
            TaskPagesTests.user
        )

        response_empty_group = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={
                    'slug': TaskPagesTests.empty_group.slug
                }
            )
        )
        self.assertTrue(not response_empty_group.context['page'])

    def test_new_and_edit_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:new_post'))
        response_edit = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={
                    'username': TaskPagesTests.user.username,
                    'post_id': TaskPagesTests.post_in_group.id
                }
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
                edit_form_field = response_edit.context['form'].fields[value]
                self.assertIsInstance(edit_form_field, expected)

        self.assertContains(
            response_edit,
            TaskPagesTests.post_in_group.text,
            count=1,
            html=True
        )

    def test_profile_page_show_correct_context(self):
        response_profile = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={
                    'username': TaskPagesTests.user.username
                }
            )
        )
        response_post = self.authorized_client.get(
            reverse(
                'posts:post',
                kwargs={
                    'username': TaskPagesTests.user.username,
                    'post_id': TaskPagesTests.post_in_group.id
                }
            )
        )

        context_profile_author = response_profile.context['author']
        context_profile_post = response_profile.context['page'][0]
        context_post_author = response_post.context['author']
        context_post_post = response_post.context['post']

        self.assertEqual(
            context_profile_author,
            TaskPagesTests.user
        )
        self.assertEqual(
            context_profile_post.text,
            TaskPagesTests.post_in_group.text
        )
        self.assertEqual(
            context_post_author,
            TaskPagesTests.user
        )
        self.assertEqual(
            context_post_post.text,
            TaskPagesTests.post_in_group.text
        )

    def test_imagine_in_context(self):
        reverse_to_test = [
            reverse('posts:index'),
            reverse(
                'posts:profile',
                kwargs={'username': TaskPagesTests.user.username}),
            reverse(
                'posts:group_posts',
                kwargs={'slug': TaskPagesTests.group.slug}),
        ]

        for reverse_name in reverse_to_test:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                image_context = response.context['page'][0]
                self.assertEqual(
                    image_context.image,
                    'posts/small.gif'
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
        self.guest_client = Client()

    def test_paginator(self):
        reverse_to_posts_count = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': PaginatorViewsTest.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user.username})
        ]
        # first page contains ten records
        for reverse_name in reverse_to_posts_count:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page']), 10)

        # second page contains one records
        for reverse_name in reverse_to_posts_count:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page']), 1)


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

        cls.post = Post.objects.create(
            text='В тестовой группе содержится тестовый пост',
            author=user,
        )

    def setUp(self):
        cache.delete('index_page')
        self.guest_client = Client()

    def test_cache(self):
        self.guest_client.get(reverse('posts:index'))
        Post.objects.create(text='text', author=TaskCacheTests.user)

        response2 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response2.context['page']), 1)

        cache.delete('index_page')
        response3 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response3.context['page']), 2)


class TaskFollowTests(TestCase):
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
            'test_authorized_user1',
            'authorized@user1.ru',
            'user1'
        )
        user2.last_name = 'usered'
        user2.save()
        cls.user2 = user2

        user3 = User.objects.create_user(
            'test_authorized_user2',
            'authorized@user2.ru',
            'user2'
        )
        user3.last_name = 'usered'
        user3.save()
        cls.user3 = user3

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=user
        )
        cls.post = Post.objects.create(
            text='Тестовый пост от второго юзера',
            author=user2
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskFollowTests.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(TaskFollowTests.user2)
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(TaskFollowTests.user3)

    def test_follow_unfollow(self):
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TaskFollowTests.user2.username}
            )
        )

        self.assertTrue(
            Follow.objects.filter(
                user=TaskFollowTests.user,
                author=TaskFollowTests.user2
            ).exists()
        )

        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': TaskFollowTests.user2.username}
            )
        )

        self.assertTrue(
            not Follow.objects.filter(
                user=TaskFollowTests.user,
                author=TaskFollowTests.user2
            ).exists()
        )

    def test_follow_index(self):
        Follow.objects.create(
            user=TaskFollowTests.user,
            author=TaskFollowTests.user2
        )

        response_follow_exist = self.authorized_client.get(
            reverse('posts:follow_index')
        )

        self.assertEqual(
            len(response_follow_exist.context['page']),
            1
        )

        response_follow_not_exist = self.authorized_client3.get(
            reverse('posts:follow_index')
        )

        self.assertEqual(
            len(response_follow_not_exist.context['page']),
            0
        )

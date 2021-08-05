import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEST_DIR = 'test_data'


@override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
class TaskFormTests(TestCase):
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

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=user
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskFormTests.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый пост',
            'group': TaskFormTests.group.id,
            'image': TaskFormTests.image
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse('posts:index'))

        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image, 'posts/small.gif')

    def test_empty_text(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': ''
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(response, 'form', 'text', 'Обязательное поле.')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_form_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый пост',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'username': TaskFormTests.user.username,
                    'post_id': TaskFormTests.post.id,
                }
            ),
            data=form_data,
            follow=True
        )

        new_text = Post.objects.get(pk=TaskFormTests.post.id).text
        self.assertRedirects(
            response,
            reverse(
                'posts:post',
                kwargs={
                    'username': TaskFormTests.user.username,
                    'post_id': TaskFormTests.post.id
                }
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(new_text, form_data['text'])

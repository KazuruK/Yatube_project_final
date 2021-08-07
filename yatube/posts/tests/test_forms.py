import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEST_DIR = 'test_data'
REDIRECT = '/auth/login/?next='
INDEX_URL = reverse('posts:index')
NEW_POST_URL = reverse('posts:new_post')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
class TaskPostFormTests(TestCase):
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
        user2 = User.objects.create_user(
            'test_user',
            'admin@admin.com',
            'admin'
        )
        user2.last_name = 'adminov'
        user2.save()
        cls.user2 = user2
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(user2)
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание группы'
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test2',
            description='Тестовое описание группы 2'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=user,
            group=TaskPostFormTests.group
        )
        cls.POST_URL = reverse(
            'posts:post',
            kwargs={
                'username': user.username,
                'post_id': TaskPostFormTests.post.id
            }
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={
                'username': user.username,
                'post_id': TaskPostFormTests.post.id
            }
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_guest_create_post(self):
        posts_count = Post.objects.count()
        pk_before_create = Post.objects.values_list('pk', flat=True)
        form_data_guest = {
            'text': 'Новый тестовый гостевой пост',
            'group': self.group.id,
            'image': self.image
        }
        response_guest = self.guest_client.post(
            NEW_POST_URL,
            data=form_data_guest,
            follow=True
        )
        self.assertRedirects(response_guest, REDIRECT + NEW_POST_URL)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(
            len(Post.objects.values_list('pk', flat=True)),
            len(pk_before_create)
        )

    def test_create_post(self):
        posts_count = Post.objects.count()
        pk_before_create = Post.objects.values_list('pk', flat=True)
        form_data = {
            'text': 'Новый тестовый пост',
            'group': self.group.id,
            'image': self.image
        }
        response = self.authorized_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, INDEX_URL)
        pk_after_create = Post.objects.values_list('pk', flat=True)
        for pk in pk_after_create:
            if pk not in pk_before_create:
                post = Post.objects.get(pk=pk)
                self.assertEqual(post.text, form_data['text'])
                self.assertEqual(post.group.id, form_data['group'])
                self.assertEqual(post.image, 'posts/small.gif')
                self.assertEqual(post.author, self.user)
                break

    def test_form_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый пост',
            'group': self.group2.id,
        }
        list_test = [
            [
                self.guest_client,
                REDIRECT + self.POST_EDIT_URL,
                [self.post.text, self.post.group, self.user]
            ],
            [
                self.authorized_client2,
                self.POST_URL,
                [self.post.text, self.post.group, self.user]
            ],
            [
                self.authorized_client,
                self.POST_URL,
                [form_data['text'], self.group2, self.user]
            ],
        ]
        for test in list_test:
            with self.subTest(test=test):
                response = test[0].post(
                    self.POST_EDIT_URL,
                    data=form_data,
                    follow=True
                )
                new_post = Post.objects.get(pk=self.post.id)
                self.assertRedirects(
                    response,
                    test[1]
                )
                self.assertEqual(Post.objects.count(), posts_count)
                self.assertEqual(new_post.text, test[2][0])
                self.assertEqual(new_post.group, test[2][1])
                self.assertEqual(new_post.author, test[2][2])

    def test_new_page_show_correct_context(self):
        response = self.authorized_client.get(NEW_POST_URL)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        response_edit = self.authorized_client.get(self.POST_EDIT_URL)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                edit_form_field = response_edit.context['form'].fields[value]
                self.assertIsInstance(edit_form_field, expected)
        self.assertEqual(
            response_edit.context['post'],
            self.post
        )


class TaskCommentFormTests(TestCase):
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
            'test_user',
            'admin@admin.com',
            'admin'
        )
        user2.last_name = 'adminov'
        user2.save()
        cls.user2 = user2
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(user2)
        cls.form_fields = {
            'text': forms.fields.CharField,
        }
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=user,
        )
        cls.POST_URL = reverse(
            'posts:post',
            kwargs={
                'username': user.username,
                'post_id': TaskCommentFormTests.post.id
            }
        )
        cls.POST_COMMENT_URL = reverse(
            'posts:add_comment',
            kwargs={
                'username': user.username,
                'post_id': TaskCommentFormTests.post.id
            }
        )

    def test_create_comment(self):
        pk_before_create = Comment.objects.values_list('pk', flat=True)
        form_data = {
            'text': 'Новый тестовый комментарий',
        }
        list_tests = [
            [self.guest_client, REDIRECT + self.POST_COMMENT_URL],
            [
                self.authorized_client,
                self.POST_URL,
                [form_data['text'], self.user, self.post]
            ],
            [
                self.authorized_client2,
                self.POST_URL,
                [form_data['text'], self.user2, self.post]
            ],
        ]
        for test in list_tests:
            with self.subTest(test=test):
                response = test[0].post(
                    self.POST_COMMENT_URL,
                    data=form_data,
                    follow=True
                )
                self.assertRedirects(response, test[1])
                pk_after_create = Comment.objects.values_list('pk', flat=True)
                if pk_after_create == pk_before_create:
                    continue
                for pk in pk_after_create:
                    if pk not in pk_before_create:
                        comment = Comment.objects.get(pk=pk)
                        self.assertEqual(comment.text, test[2][0])
                        self.assertEqual(comment.author, test[2][1])
                        self.assertEqual(comment.post, test[2][2])
                        break

    def test_comment_page_show_correct_context(self):
        response = self.authorized_client.get(self.POST_URL)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

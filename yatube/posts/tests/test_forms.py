import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEST_DIR = 'test_data'
REDIRECT = reverse('login') + '?next='
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
            group=cls.group
        )
        cls.POST_URL = reverse(
            'posts:post',
            args=[user.username, cls.post.id]
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[user.username, cls.post.id]
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_guest_create_post(self):
        posts_count = Post.objects.count()
        all_pk_before_create = Post.objects.values_list('pk', flat=True)
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
            set(Post.objects.values_list('pk', flat=True)),
            set(all_pk_before_create)
        )

    def test_create_post(self):
        form_data = {
            'text': 'Новый тестовый пост',
            'group': self.group.id,
            'image': self.image
        }
        all_post_pk_before_create = Post.objects.values_list('pk', flat=True)
        all_post_pk_before_create_count = len(all_post_pk_before_create)
        response = self.authorized_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        all_post_pk_after_create = Post.objects.values_list('pk', flat=True)
        self.assertRedirects(response, INDEX_URL)
        self.assertEqual(
            all_post_pk_after_create.count(),
            all_post_pk_before_create_count + 1
        )
        posts = [
            post
            for post in response.context['page']
            if post.id not in all_post_pk_before_create
        ]
        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image, 'posts/small.gif')
        self.assertEqual(post.author, self.user)

    def test_form_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый пост',
            'group': self.group2.id,
        }
        client_url_values = [
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
        for client, url, (text, group, user) in client_url_values:
            with self.subTest(
                client=client,
                url=url,
                text=text,
                group=group,
                user=user
            ):
                response = client.post(
                    self.POST_EDIT_URL,
                    data=form_data,
                    follow=True
                )
                self.assertRedirects(
                    response,
                    url
                )
                if 'post' not in response.context:
                    continue
                new_post = response.context['post']
                self.assertEqual(Post.objects.count(), posts_count)
                self.assertEqual(new_post.text, text)
                self.assertEqual(new_post.group, group)
                self.assertEqual(new_post.author, user)

    def test_new_and_edit_page_show_correct_context(self):
        urls = [NEW_POST_URL, self.POST_EDIT_URL]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                for value, expected in self.form_fields.items():
                    with self.subTest(value=value, expected=expected):
                        form_field = response.context['form'].fields[value]
                        self.assertIsInstance(form_field, expected)
                if url == self.POST_EDIT_URL:
                    self.assertEqual(
                        response.context['post'],
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
            args=[user.username, cls.post.id]
        )
        cls.POST_COMMENT_URL = reverse(
            'posts:add_comment',
            args=[user.username, cls.post.id]
        )

    def test_create_comment(self):
        form_data = {
            'text': 'Новый тестовый комментарий',
        }
        list_tests = [
            [self.guest_client, REDIRECT + self.POST_COMMENT_URL,
             [None, None, None]],
            [self.authorized_client, self.POST_URL,
             [form_data['text'], self.user, self.post]],
            [self.authorized_client2, self.POST_URL,
             [form_data['text'], self.user2, self.post]],
        ]
        for client, url, (text, user, post) in list_tests:
            with self.subTest(
                client=client,
                url=url,
                text=text,
                user=user,
                post=post
            ):
                all_pk_before_create = Comment.objects.values_list(
                    'pk',
                    flat=True
                )
                response = client.post(
                    self.POST_COMMENT_URL,
                    data=form_data,
                    follow=True
                )
                all_pk_after_create = Comment.objects.values_list(
                    'pk',
                    flat=True
                )
                self.assertRedirects(response, url)
                if len(all_pk_after_create) == len(all_pk_before_create):
                    continue
                self.assertEqual(
                    len(all_pk_after_create),
                    len(all_pk_before_create) + 1
                )
                comments = [
                    comment
                    for comment in response.context['post'].comments.all()
                    if comment.id not in all_pk_before_create
                ]
                self.assertEqual(len(comments), 1)
                comment = comments[0]
                self.assertEqual(comment.text, text)
                self.assertEqual(comment.author, user)
                self.assertEqual(comment.post, post)

    def test_comment_page_show_correct_context(self):
        response = self.authorized_client.get(self.POST_URL)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

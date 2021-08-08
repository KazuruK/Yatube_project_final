from django.test import TestCase

from ..models import Comment, Follow, Group, Post, User


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug='test'
        )

    def test_verbose_name(self):
        field_verbose_group = {
            'title': 'Название',
            'description': 'Описание',
            'slug': 'Уникальный идентификатор группы'
        }
        for field, expected_value in field_verbose_group.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Group._meta.get_field(field).verbose_name, expected_value)

    def test_group_to_string(self):
        self.assertEqual(self.group.title, str(self.group))


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user('admin', 'admin@admin.com', 'admin')
        user.last_name = 'adminov'
        user.save()
        cls.post = Post.objects.create(
            text='Тестовый пост который больше 15 символов',
            author=user
        )

    def test_verbose_name(self):
        field_verbose_post = {
            'group': 'Группа',
            'text': 'Текст поста',
            'pub_date': 'Дата создания',
            'author': 'Автор',
            'image': 'Изображение'
        }
        for field, expected_value in field_verbose_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name, expected_value)

    def test_post_to_string(self):
        self.assertEqual(self.post.text[:15], str(self.post))


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user('admin', 'admin@admin.com', 'admin')
        user.last_name = 'adminov'
        user.save()
        cls.post = Post.objects.create(
            text='Тестовый пост который больше 15 символов',
            author=user
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=user,
            text='Тестовый комментарий больше 15 символов'
        )

    def test_verbose_name(self):
        field_verbose_post = {
            'post': 'К посту:',
            'author': 'Автор комментария',
            'text': 'Комментарий',
            'created': 'Дата создания',
        }
        for field, expected_value in field_verbose_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Comment._meta.get_field(field).verbose_name, expected_value
                )

    def test_post_to_string(self):
        expected_value = self.comment.text[:15]
        self.assertEqual(expected_value, str(self.comment))


class FollowModelTest(TestCase):
    def test_verbose_name(self):
        field_verbose_post = {
            'user': 'Подписчик',
            'author': 'Блогер',
        }
        for field, expected_value in field_verbose_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Follow._meta.get_field(field).verbose_name, expected_value)

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы'
        )

    def test_verbose_name(self):
        group = GroupModelTest.group

        field_verbose_group = {
            'title': 'Название группы',
            'description': 'Описание группы',
        }

        for field, expected_value in field_verbose_group.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_group_to_string(self):
        group = GroupModelTest.group
        expected_value = group.title
        self.assertEqual(expected_value, str(group))


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        user = User.objects.create_user('admin', 'admin@admin.com', 'admin')
        user.last_name = 'adminov'
        user.save()

        cls.post = Post.objects.create(
            text='Тестовый пост который больше 15 символов',
            author=user
        )

    def test_verbose_name(self):
        post = PostModelTest.post

        field_verbose_post = {
            'group': 'Группа',
            'text': 'Текст поста',
            'author': 'Автор'
        }

        for field, expected_value in field_verbose_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_post_to_string(self):
        post = PostModelTest.post
        expected_value = post.text[:15]
        self.assertEqual(expected_value, str(post))

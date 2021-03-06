from autoslug.settings import slugify
from django import forms

from .models import Comment, Post, Group


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': 'Текст тут',
            'group': 'Группа',
            'image': 'Изображение'
        }
        help_texts = {
            'text': 'Вы можете рассказать нам о своем дне, '
                    'или о том какая у вас замечательная собака',
            'group': 'Выберете группу для публикации, если хотите :^)',
            'image': 'Хотите ли вы проиллюстрировать свой пост?'
        }


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['title', 'slug', 'description']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

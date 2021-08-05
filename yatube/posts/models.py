"""Database interaction models."""
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """
    Stores one group where users can submit their posts.
    No strict relate.
    """

    title = models.CharField(max_length=200, verbose_name='Название группы')
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True,
                                   verbose_name='Описание группы')

    def __str__(self):
        """
        Overriding base __str__. Outputs the name of the group.
        """
        return self.title


class Post(models.Model):
    """
    Stores one user or admin post.
    Related to: model: `group.Group` and: model:` auth.User`.
    """

    group = models.ForeignKey(Group, blank=True, null=True,
                              on_delete=models.SET_NULL,
                              related_name='group_posts',
                              verbose_name='Группа')
    text = models.TextField(verbose_name='Текст поста', blank=False)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts', verbose_name='Автор')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        """
        Overriding base __str__.
        """
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField(verbose_name="Комментарий", blank=False)
    created = models.DateTimeField('date published', auto_now_add=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following")

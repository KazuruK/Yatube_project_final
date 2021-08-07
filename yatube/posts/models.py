"""Database interaction models."""
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """
    Stores one group where users can submit their posts.
    No strict relate.
    """

    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True,
                            verbose_name='Уникальный адрес')
    description = models.TextField(blank=True, null=True,
                                   verbose_name='Описание')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

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
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата создания')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts', verbose_name='Автор')
    image = models.ImageField(upload_to='posts/', blank=True, null=True,
                              verbose_name='Изображение')

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        """
        Overriding base __str__.
        """
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name='К посту:')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Автор комментария')
    text = models.TextField(verbose_name='Комментарий', blank=False)
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата создания')

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Подписан')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

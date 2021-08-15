"""Creation of interfaces for site administrators, in order to control,
   change and create posts and groups."""
from django.contrib import admin

from .models import Comment, FollowAuthor, Group, Post, FollowGroup


class GroupAdmin(admin.ModelAdmin):
    """
    This class creates an interface for administering Groups.

    Displays all group parameters.
    Search by group name and description is also implemented. The latter was
     implemented with the aim of catching unwanted content in a timely manner.
    Implemented filtering by the unique name of the group - part of the link,
     to exclude the capture of posts from different groups with the same name.
    """

    list_display = ('title', 'slug', 'description')
    search_fields = ('title', 'description',)
    list_filter = ('slug',)
    prepopulated_fields = {"slug": ("title",)}


class PostAdmin(admin.ModelAdmin):
    """
    This class creates an interface for administering posts.

    Displays all post parameters, as well as their individual,
     unique number in the database.
    It also implemented a search by the text of the post,
     filtering by the day of adding and the groups where the post is posted.
    When an empty value is found, fills it with the value: -пусто-
    """

    list_display = ('pk', 'text', 'pub_date', 'author', 'group', 'image')
    search_fields = ('text',)
    list_filter = ('pub_date', 'group',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'author', 'post', 'created')
    search_fields = ('text', 'author')
    list_filter = ('created', 'author', 'post')
    empty_value_display = '-пусто-'


class FollowAuthorAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')
    empty_value_display = '-пусто-'


class FollowGroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'group')
    search_fields = ('user', 'group')
    list_filter = ('user', 'group')
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(FollowAuthor, FollowAuthorAdmin)
admin.site.register(FollowGroup, FollowGroupAdmin)

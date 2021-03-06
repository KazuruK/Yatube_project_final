"""yatube URL Configuration.
   The page addresses processed by the posts application's View functions."""
from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path('',
         views.index,
         name='index'),
    path(
        'group/',
        views.all_groups,
        name='all_groups'),
    path('group/<slug:slug>/',
         views.group_posts,
         name='group_posts'),
    path('group/<slug:slug>/follow/',
         views.group_follow,
         name='group_follow'),
    path('group/<slug:slug>/unfollow/',
         views.group_unfollow,
         name='group_unfollow'),
    path('new/',
         views.new_post,
         name='new_post'),
    path('new_group/',
         views.new_group,
         name='new_group'),
    path('follow/',
         views.follow_index,
         name='follow_index'),
    path('<str:username>/',
         views.profile,
         name='profile'),
    path('<str:username>/follow/',
         views.profile_follow,
         name='profile_follow'),
    path('<str:username>/unfollow/',
         views.profile_unfollow,
         name='profile_unfollow'),
    path('<str:username>/<int:post_id>/',
         views.post_view,
         name='post'),
    path('<str:username>/<int:post_id>/edit/',
         views.post_edit,
         name='post_edit'),
    path('<str:username>/<int:post_id>/comment/',
         views.add_comment,
         name='add_comment'),
]

"""yatube URL Configuration.
   The page addresses processed by the posts application's View functions."""
from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path('', views.index, name='index'),
    # Отображение всех групп
    path('group/', views.all_groups, name='all_groups'),
    # Отображение всех записей группы
    path('group/<slug:slug>/', views.group_posts, name='group_posts'),
    # Создание нового поста
    path('new/', views.new_post, name='new_post'),
    # Просмотр ленты по подпискам
    path("follow/", views.follow_index, name="follow_index"),
    # Профайл пользователя
    path('<str:username>/', views.profile, name='profile'),
    # Создание подписки на пользователя
    path("<str:username>/follow/", views.profile_follow,
         name="profile_follow"),
    # Отписка от пользователя
    path("<str:username>/unfollow/", views.profile_unfollow,
         name="profile_unfollow"),
    # Просмотр записи
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),
    # Редактирование записи
    path('<str:username>/<int:post_id>/edit/', views.post_edit,
         name='post_edit'),
    # Добавление комментария
    path("<username>/<int:post_id>/comment/", views.add_comment,
         name="add_comment")
]

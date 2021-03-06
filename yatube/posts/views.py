"""View-functions for describing the inner workings of the site pages."""
from autoslug.settings import slugify
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from .forms import CommentForm, PostForm, GroupForm
from .models import FollowAuthor, Group, Post, User, FollowGroup


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@require_GET
def index(request):
    post_list = cache.get('index_page')
    if post_list is None:
        post_list = Post.objects.all()
        cache.set('index_page', post_list, timeout=20)
    paginator = Paginator(post_list, settings.PAGINATOR_POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/index.html', {'page': page})


def all_groups(request):
    groups = Group.objects.all()
    paginator = Paginator(groups, settings.PAGINATOR_POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/groups.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.group_posts.all()
    paginator = Paginator(posts_list, settings.PAGINATOR_POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/group.html', {'group': group, 'page': page})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.all()
    paginator = Paginator(posts_list, settings.PAGINATOR_POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = (
            request.user.is_authenticated
            and author != request.user
            and FollowAuthor.objects.filter(
            user=request.user,
            author=author
        ).exists()
    )
    return render(request, 'posts/profile.html', {
        'author': author,
        'page': page,
        'following': following
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    following = (
            request.user.is_authenticated
            and post.author != request.user
            and FollowAuthor.objects.filter(
            user=request.user,
            author=post.author
        ).exists()
    )
    return render(request, 'posts/post.html', {
        'author': post.author,
        'post': post,
        'form': form,
        'following': following
    })


@login_required
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('posts:post', username=username, post_id=post_id)
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post', username=username, post_id=post_id)
    return render(request, 'posts/new_post.html', {
        'post': post,
        'form': form,
        'edit': True
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_form = form.save(commit=False)
        new_form.author = request.user
        new_form.save()
        return redirect('posts:index')
    return render(request, 'posts/new_post.html', {
        'form': form,
        'edit': False
    })


@login_required
def new_group(request):
    form = GroupForm(request.POST or None)
    if form.is_valid():
        new_form = form.save(commit=False)
        new_form.save()
        return redirect('posts:group_posts', slug=new_form.slug)
    return render(request, 'posts/new_group.html', {'form': form})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('posts:post', username=username,
                    post_id=post_id)


@require_GET
@login_required
def follow_index(request):
    follow_author_list = Post.objects.filter(
        author__following__user=request.user
    )
    follow_group_list = Post.objects.filter(
        group__group_following__user=request.user
    )
    follow_post_list = follow_author_list | follow_group_list
    paginator = Paginator(follow_post_list, settings.PAGINATOR_POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user and not FollowAuthor.objects.filter(
        author=author,
        user=user
    ).exists():
        FollowAuthor.objects.create(
            user=user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        FollowAuthor,
        author__username=username,
        user=request.user
    ).delete()
    return redirect('posts:profile', username=username)


@login_required
def group_follow(request, slug):
    group = get_object_or_404(Group, slug=slug)
    user = request.user
    if not FollowGroup.objects.filter(
        user=user,
        group=group
    ).exists():
        FollowGroup.objects.create(
            user=user,
            group=group
        )
    return redirect('posts:group_posts', slug=slug)


@login_required
def group_unfollow(request, slug):
    get_object_or_404(
        FollowGroup,
        group__slug=slug,
        user=request.user
    ).delete()
    return redirect('posts:group_posts', slug=slug)

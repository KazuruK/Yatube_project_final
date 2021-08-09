from django.test import TestCase
from django.urls import reverse

GROUP_SLUG = 'test'
USERNAME = 'test_admin'
POST_ID = 1


class TaskRouteTests(TestCase):
    def test_routs(self):
        url_reverse = [
            ['/', 'posts:index',
             []],
            ['/group/', 'posts:all_groups',
             []],
            [f'/group/{GROUP_SLUG}/', 'posts:group_posts',
             [GROUP_SLUG]],
            ['/new/', 'posts:new_post',
             []],
            ['/follow/', 'posts:follow_index',
             []],
            [f'/{USERNAME}/', 'posts:profile',
             [USERNAME]],
            [f'/{USERNAME}/follow/', 'posts:profile_follow',
             [USERNAME]],
            [f'/{USERNAME}/unfollow/', 'posts:profile_unfollow',
             [USERNAME]],
            [f'/{USERNAME}/{POST_ID}/', 'posts:post',
             [USERNAME, POST_ID]],
            [f'/{USERNAME}/{POST_ID}/edit/', 'posts:post_edit',
             [USERNAME, POST_ID]],
            [f'/{USERNAME}/{POST_ID}/comment/', 'posts:add_comment',
             [USERNAME, POST_ID]],
        ]
        for url, app_name, reverse_args in url_reverse:
            with self.subTest(url=url):
                self.assertEqual(url, reverse(app_name, args=reverse_args))

from django.test import TestCase
from django.urls import reverse

GROUP_SLUG = 'test'
USERNAME = 'test_admin'
POST_ID = '1'


class TaskRoutTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_routs(self):
        url_reverse = {
            '/': reverse('posts:index'),
            '/group/': reverse('posts:all_groups'),
            f'/group/{GROUP_SLUG}/': reverse(
                'posts:group_posts',
                kwargs={'slug': GROUP_SLUG}
            ),
            '/new/': reverse('posts:new_post'),
            '/follow/': reverse('posts:follow_index'),
            f'/{USERNAME}/': reverse(
                'posts:profile',
                kwargs={'username': USERNAME}
            ),
            f'/{USERNAME}/follow/': reverse(
                'posts:profile_follow',
                kwargs={'username': USERNAME}
            ),
            f'/{USERNAME}/unfollow/': reverse(
                'posts:profile_unfollow',
                kwargs={'username': USERNAME}
            ),
            f'/{USERNAME}/{POST_ID}/': reverse(
                'posts:post',
                kwargs={'username': USERNAME, 'post_id': POST_ID}
            ),
            f'/{USERNAME}/{POST_ID}/edit/': reverse(
                'posts:post_edit',
                kwargs={'username': USERNAME, 'post_id': POST_ID}
            ),
            f'/{USERNAME}/{POST_ID}/comment/': reverse(
                'posts:add_comment',
                kwargs={'username': USERNAME, 'post_id': POST_ID}),
        }
        for url, reverse_name in url_reverse.items():
            with self.subTest(url=url):
                self.assertEqual(url, reverse_name)

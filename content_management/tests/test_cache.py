from django.test import TestCase
from config.settings.base import redis

from blog.users.models import User
from content_management.caches import ContentCache
from content_management.models import Content, Like


class TestContentCache(TestCase):
    def setUp(self):
        redis.select(15)
        self.conn = redis
        self.conn.flushdb()
        self._create_users()
        self._create_contents()
        self._create_likes()
        self._create_likes()

    @staticmethod
    def _create_users():
        users = list()
        for i in range(1, 4):
            users.append(User(id=i, username=f'user {i}'))
        User.objects.bulk_create(users)

    @staticmethod
    def _create_contents():
        contents = list()
        for i in range(1, 4):
            contents.append(
                Content(id=i, title=f'title {i}', text=f'text {i}'))
        Content.objects.bulk_create(contents)

    @staticmethod
    def _create_likes():
        '''
        Content id | user like | like value
        Content 1 | 1 | 5
        Content 2 | 1 | 2
        Content 2 | 2 | 0
        Content 2 | 3 | 5

        Result:
        Content id | like count | like avg
        1 | 1 | 5
        2 | 3 | 3
        3 | 0 | 0
        '''
        likes = [
            Like(content_id=1, user_id=1, value=5),
            Like(content_id=2, user_id=1, value=2),
            Like(content_id=2, user_id=2, value=0),
            Like(content_id=2, user_id=3, value=4),
        ]
        Like.objects.bulk_create(likes)

    def _get_cache(self):
        return ContentCache(self.conn)

    def test_before_build_cache_is_empty(self):
        cache = self._get_cache()
        result = cache.list(range(1, 10))
        assert len(list(result)) == 0

    def test_check_cache_contents(self):
        cache = self._get_cache()
        cache.build()
        result = list(cache.list(range(1, 10)))
        assert result == [
            {'id': '1', 'title': 'title 1', 'likes_count': '1', 'likes_avg': '5.0'},
            {'id': '2', 'title': 'title 2', 'likes_count': '3', 'likes_avg': '2.0'},
            {'id': '3', 'title': 'title 3', 'likes_count': '0', 'likes_avg': '0.0'},
        ]


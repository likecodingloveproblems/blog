from unittest import mock

from django.test import TestCase
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from blog.users.models import User
from config.settings.base import redis
from content_management.caches import ContentCache
from content_management.models import Content
from content_management.models import Like
from content_management.rate_limiter import TokenBucketRateLimiter


class TestContentAPIView(TestCase):
    url = reverse_lazy("api:content")

    def setUp(self):
        self.client = APIClient()
        redis.select(15)
        redis.flushdb()
        self.user = User.objects.create_user("user 1", password="12345")  # noqa: S106

    @staticmethod
    def _get_data():
        return [
            {
                "id": f"{i}",
                "title": f"title {i}",
                "likes_count": f"{2 * i}",
                "likes_avg": f"{i}",
            }
            for i in range(1, 6)
        ]

    def _build_cache(self):
        for item in self._get_data():
            redis.hset(
                f'content:{item["id"]}',
                mapping=item,
            )

    @staticmethod
    def _get_post_body():
        return {"title": "title", "text": "text"}

    def test_empty_cache(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "from": 1,
            "to": 11,
            "items": [],
        }

    def test_successful(self):
        self._build_cache()
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "from": 1,
            "to": 11,
            "items": self._get_data(),
        }

    def test_pagination(self):
        self._build_cache()
        response = self.client.get(self.url + "?from=2&to=5")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "from": "2",
            "to": "5",
            "items": self._get_data()[1:4],
        }

    def test_user_like_value(self):
        content = Content.objects.create(id=1, title="title", text="text")
        Like.objects.create(user=self.user, content=content, value=5)
        self.client.login(username="user 1", password="12345")  # noqa: S106
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "from": 1,
            "to": 11,
            "items": [
                {
                    "id": "1",
                    "title": "title",
                    "likes_count": "1",
                    "likes_avg": "5.0",
                    "your_like_value": 5,
                },
            ],
        }

    def test_anonymous_user_can_not_create_content(self):
        response = self.client.post(self.url, data=self._get_post_body())
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_successful_create_content(self):
        self.client.login(username="user 1", password="12345")  # noqa: S106
        response = self.client.post(self.url, data=self._get_post_body())
        assert response.status_code == status.HTTP_201_CREATED
        assert Content.objects.filter(title="title", text="text").count() == 1


class TestLikeContentAPIView(TestCase):
    url = reverse_lazy("api:like-content")

    def setUp(self):
        self.user = User.objects.create_user("user 1", password="12345")  # noqa: S106
        self.content = Content.objects.create(id=1, title="title", text="text")
        self.client = APIClient()
        redis.select(15)
        redis.flushdb()
        self.conn = redis
        self.cache = ContentCache(redis)

    @staticmethod
    def _get_post_body():
        return {"content": 1, "value": 3}

    def _login(self):
        self.client.login(username="user 1", password="12345")  # noqa: S106

    def test_anonymous_user_not_allowed(self):
        response = self.client.post(self.url, data=self._get_post_body())
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_first_time_user_like_successful(self):
        self._login()
        response = self.client.post(self.url, data=self._get_post_body())
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"content": 1, "value": 3}
        result = list(self.cache.list([self.content.id]))
        assert result == [
            {
                "id": f"{self.content.id}",
                "title": "title",
                "likes_count": "1",
                "likes_avg": "3.0",
            },
        ]

    def test_update_like_successful(self):
        Like.objects.create(content=self.content, user=self.user, value=5)
        self._login()
        response = self.client.post(self.url, data=self._get_post_body())
        assert response.status_code == status.HTTP_200_OK
        result = list(self.cache.list([self.content.id]))
        assert result == [
            {
                "id": f"{self.content.id}",
                "title": "title",
                "likes_count": "1",
                "likes_avg": "3.0",
            },
        ]

    @mock.patch.object(Like, "get_rate_limiter")
    def test_rate_limited_likes(self, mocked_get_rate_limiter):
        mocked_get_rate_limiter.return_value = TokenBucketRateLimiter(
            self.conn,
            limit_count=3,
        )
        for i in range(1, 6):
            username = f"username {i}"
            password = f"password {i}"
            User.objects.create_user(username=username, password=password)
            self.client.login(username=username, password=password)
            response = self.client.post(self.url, data={"content": 1, "value": i})
            assert status.is_success(response.status_code)

        result = list(self.cache.list([1]))
        assert result == [
            {
                "id": "1",
                "title": "title",
                "likes_count": "3",
                "likes_avg": "2.0",
            },
        ]
        assert Like.objects.filter(state=Like.StateChoice.OK).count() == 3  # noqa: PLR2004
        assert Like.objects.filter(state=Like.StateChoice.RATE_LIMITED).count() == 2  # noqa: PLR2004

from django.test import TestCase
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from blog.users.models import User
from config.settings.base import redis
from content_management.models import Content


class TestContentAPIView(TestCase):
    url = reverse_lazy("api:content")

    def setUp(self):
        self.client = APIClient()
        redis.select(15)
        redis.flushdb()
        User.objects.create_user("user 1", password="12345")  # noqa: S106

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

    def test_anonymous_user_can_not_create_content(self):
        response = self.client.post(self.url, data=self._get_post_body())
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_successful_create_content(self):
        self.client.login(username="user 1", password="12345")  # noqa: S106
        response = self.client.post(self.url, data=self._get_post_body())
        assert response.status_code == status.HTTP_201_CREATED
        assert Content.objects.filter(title="title", text="text").count() == 1

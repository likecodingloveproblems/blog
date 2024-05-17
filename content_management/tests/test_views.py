from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from config.settings.base import redis


class TestContentListAPIView(TestCase):
    def setUp(self):
        self.client = APIClient()
        redis.select(15)
        redis.flushdb()

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

    def test_empty_cache(self):
        response = self.client.get(reverse("api:content-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "from": 1,
            "to": 11,
            "items": [],
        }

    def test_successful(self):
        self._build_cache()
        response = self.client.get(reverse("api:content-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "from": 1,
            "to": 11,
            "items": self._get_data(),
        }

    def test_pagination(self):
        self._build_cache()
        response = self.client.get(reverse("api:content-list") + "?from=2&to=5")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "from": "2",
            "to": "5",
            "items": self._get_data()[1:4],
        }

from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from blog.users.models import User
from config.settings.base import redis
from content_management.caches import ContentCache
from content_management.models import Content
from content_management.models import Like
from content_management.serializers import ContentSerializer
from content_management.serializers import LikeContentSerializer


class ContentAPIView(APIView):
    serializer_class = ContentSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_ids(self, request) -> list[int]:
        self.from_ = request.GET.get("from")
        self.to = request.GET.get("to")
        if self.from_ is None or self.to is None:
            self.to = max(redis.get(Content.redis_max_id_key) or 11, 11)
            self.from_ = max(self.to - 10, 1)
        return range(int(self.from_), int(self.to))

    @staticmethod
    def _add_user_values(user: User, data: list[dict]):
        # TODO: it can be moved to the cache layer for the performance sake!
        ids = [content["id"] for content in data]
        likes = Like.objects.filter(user_id=user.id, content_id__in=ids).values(
            "content_id",
            "value",
        )
        likes = {like["content_id"]: like["value"] for like in likes}
        for content in data:
            content["your_like_value"] = likes.get(int(content["id"]), None)

    def get(self, request):
        cache = ContentCache(redis)
        data = cache.list(ids=self.get_ids(request))
        if request.user.is_authenticated:
            self._add_user_values(request.user, data)
        data = {
            "items": data,
            "from": self.from_,
            "to": self.to,
        }
        return Response(data=data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class LikeContentAPIView(APIView):
    serializer_class = LikeContentSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"user_id": request.user.id},
        )
        serializer.is_valid(raise_exception=True)
        _, status_code = serializer.save()
        return Response(data=serializer.data, status=status_code)

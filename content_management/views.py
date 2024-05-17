from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.settings.base import redis
from content_management.caches import ContentCache
from content_management.models import Content

from content_management.serializers import ContentSerializer, LikeContentSerializer


class ContentListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_ids(self, request) -> list[int]:
        self.from_ = request.GET.get('from')
        self.to = request.GET.get('to')
        if self.from_ is None or self.to is None:
            self.to = max(redis.get(Content.redis_max_id_key) or 11, 11)
            self.from_ = max(self.to - 10, 1)
        return range(int(self.from_), int(self.to))

    def get(self, request):
        cache = ContentCache(redis)
        data = {
            'items': cache.list(ids=self.get_ids(request)),
            'from': self.from_,
            'to': self.to,
        }
        return Response(
            data=data,
            status=status.HTTP_200_OK)


class ContentCreateAPIView(APIView):
    serializer_class = ContentSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class LikeContentAPIView(APIView):
    serializer_class = LikeContentSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'user_id': request.user.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

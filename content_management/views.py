from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.settings.base import redis
from content_management.caches import ContentCache
from content_management.models import Content

from content_management.serializers import ContentSerializer, LikeContentSerializer


class ContentListAPIView(APIView):
    @staticmethod
    def get_ids(request) -> list[int]:
        from_ = request.GET.get('from')
        to = request.GET.get('to')
        if from_ is None or to is None:
            to = max(redis.get(Content.redis_max_id_key) or 11, 11)
            from_ = max(to - 10, 1)
        return range(from_, to)
    def get(self, request):
        cache = ContentCache(redis)
        return cache.list(ids=self.get_ids(request))


class ContentCreateAPIView(APIView):
    serializer_class = ContentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class LikeContentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LikeContentSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'user_id': request.user.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

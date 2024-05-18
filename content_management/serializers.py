from rest_framework import serializers
from rest_framework import status

from content_management.models import Content
from content_management.models import Like


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ["id", "title", "text"]


class LikeContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["content", "value"]

    def save(self, **kwargs) -> tuple[Like, int]:
        user_id = self.context["user_id"]
        if like := Like.objects.filter(
            user_id=user_id,
            content=self.validated_data["content"],
            state=Like.StateChoice.OK,
        ).first():
            # update value
            like.value = self.validated_data["value"]
            like.save(update_fields=["value"])
            return like, status.HTTP_200_OK
        like = Like(
            user_id=user_id,
            content=self.validated_data["content"],
            value=self.validated_data["value"],
        )
        like.save(**kwargs)
        return like, status.HTTP_201_CREATED

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer

from content_management.models import Content, Like


class ContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Content
        fields = ['id', 'title', 'text']


class LikeContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Like
        fields = ['content_id', 'value']

    def save(self, **kwargs):
        user_id = self.context['user_id']
        like = Like(user_id=user_id,
                    content_id=self.validated_data['content_id'],
                    value=self.validated_data['value'])
        like.save(**kwargs)


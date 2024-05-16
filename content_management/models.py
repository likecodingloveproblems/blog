from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_lifecycle import LifecycleModel, hook, AFTER_UPDATE, AFTER_CREATE
from django_lifecycle.conditions import WhenFieldHasChanged

from blog.users.models import User
from config.settings.base import redis


class Content(models.Model):
    redis_max_id_key = 'content:max_id'
    title = models.CharField(verbose_name=_('title'), max_length=50)
    text = models.TextField(verbose_name=_('text'))

    @hook(AFTER_CREATE)
    def update_max_id(self):
        if self.id and self.id > int(redis.get(self.redis_max_id_key)):
            redis.set(self.redis_max_id_key, self.id)


class Like(LifecycleModel):
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField(verbose_name=_('value'),
        validators=(MinValueValidator(limit_value=0), MaxValueValidator(limit_value=5),)
    )

    @staticmethod
    def get_cache():
        """Get cache instance
        TODO: maybe it can be cached in python!"""
        from content_management.caches import ContentCache
        return ContentCache(redis)

    @hook(AFTER_CREATE)
    def update_cache(self):
        cache = self.get_cache()
        cache.content_liked(self)

    @hook(AFTER_UPDATE,
          condition=WhenFieldHasChanged('value', has_changed=True),
          )
    def update_content_like_cache(self):
        cache = self.get_cache()
        cache.like_value_updated(self)

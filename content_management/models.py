from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_CREATE
from django_lifecycle import AFTER_UPDATE
from django_lifecycle import LifecycleModel
from django_lifecycle import hook
from django_lifecycle.conditions import WhenFieldHasChanged

from blog.users.models import User
from config.settings.base import redis
from content_management.rate_limiter import TokenBucketRateLimiter


class Content(models.Model):
    redis_max_id_key = "content:max_id"
    title = models.CharField(verbose_name=_("title"), max_length=50)
    text = models.TextField(verbose_name=_("text"))

    def __str__(self):
        return f"{self.title}: {self.text[:50]}"

    @hook(AFTER_CREATE)
    def update_max_id(self):
        if self.id and self.id > int(redis.get(self.redis_max_id_key)):
            redis.set(self.redis_max_id_key, self.id)


class Like(LifecycleModel):
    class StateChoice(models.IntegerChoices):
        OK = 1
        RATE_LIMITED = 2

    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField(
        verbose_name=_("value"),
        validators=(
            MinValueValidator(limit_value=0),
            MaxValueValidator(limit_value=5),
        ),
    )
    state = models.IntegerField(
        verbose_name=_("state"),
        choices=StateChoice.choices,
        default=StateChoice.OK,
    )

    def __str__(self):
        return f"{self.content}: {self.value}"

    @staticmethod
    def get_cache():
        """Get cache instance
        TODO: maybe it can be cached in python!"""
        from content_management.caches import ContentCache

        return ContentCache(redis)

    @staticmethod
    def get_rate_limiter():
        return TokenBucketRateLimiter(conn=redis)

    def _get_rate_limiter_key(self) -> str:
        return f"like:rate-limiter:content_id:{self.content_id}"

    @hook(AFTER_CREATE)
    def update_cache(self):
        rate_limiter = self.get_rate_limiter()
        if rate_limiter.is_limited(self._get_rate_limiter_key()):
            self.state = Like.StateChoice.RATE_LIMITED
            return
        cache = self.get_cache()
        cache.content_liked(self)

    @hook(
        AFTER_UPDATE,
        condition=WhenFieldHasChanged("value", has_changed=True),
    )
    def update_content_like_cache(self):
        cache = self.get_cache()
        cache.like_value_updated(self)

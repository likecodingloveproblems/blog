from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from blog.users.models import User


class Content(models.Model):
    title = models.CharField(verbose_name=_('title'), max_length=50)
    text = models.TextField(verbose_name=_('text'))


class Like(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField(verbose_name=_('value'),
        validators=(MinValueValidator(limit_value=0), MaxValueValidator(limit_value=5),)
    )

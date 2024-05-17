from django.urls import path

from content_management.views import ContentAPIView
from content_management.views import LikeContentAPIView

app_name = "content_management"
urlpatterns = [
    path("content/", view=ContentAPIView.as_view(), name="content"),
    path("like-content/", view=LikeContentAPIView.as_view(), name="content-like"),
]

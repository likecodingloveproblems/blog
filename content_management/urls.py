from django.urls import path

from content_management.views import ContentCreateAPIView
from content_management.views import ContentListAPIView
from content_management.views import LikeContentAPIView

app_name = "content_management"
urlpatterns = [
    path("content/", view=ContentListAPIView.as_view(), name="content-list"),
    path("content/", view=ContentCreateAPIView.as_view(), name="content-create"),
    path("like-content/", view=LikeContentAPIView.as_view(), name="content-like"),
]

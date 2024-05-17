from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from blog.users.api.views import UserViewSet
from content_management.urls import urlpatterns as content_management_urlpatterns

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)


app_name = "api"
urlpatterns = router.urls + content_management_urlpatterns

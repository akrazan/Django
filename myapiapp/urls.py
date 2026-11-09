from django.urls import path, include

from rest_framework.routers import DefaultRouter

from myapiapp.views import UserViewSet, GroupViewSet

app_name = "myapiapp"

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
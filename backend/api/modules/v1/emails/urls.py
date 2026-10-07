from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmailLogViewSet

router = DefaultRouter()
router.register('email-logs', EmailLogViewSet, basename='email-log')

urlpatterns = [
    path('', include(router.urls)),
]

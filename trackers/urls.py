from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrackerViewSet

router = DefaultRouter()
router.register(r'trackers', TrackerViewSet, basename='tracker')

urlpatterns = [
    path('', include(router.urls)),
]

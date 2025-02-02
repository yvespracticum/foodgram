from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FoodgramUserViewSet

router = DefaultRouter()
router.register(r'', FoodgramUserViewSet)

urlpatterns = [
    path('', include(router.urls)),

]

from django.contrib import admin
from django.urls import include, path
from foodapp.views import FoodgramUserViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', FoodgramUserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/users/', include(router.urls)),
]

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from foodapp.views import (FoodgramUserViewSet,
                           MySubscriptionsView,
                           SubscribeView)

router = DefaultRouter()
router.register(r'users', FoodgramUserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/users/subscriptions/', MySubscriptionsView.as_view()),
    path('api/users/<int:id>/subscribe/', SubscribeView.as_view()),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

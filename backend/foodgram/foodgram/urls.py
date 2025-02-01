from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Для авторизации через токены
    path('api/auth/', include('djoser.urls.authtoken')),
]

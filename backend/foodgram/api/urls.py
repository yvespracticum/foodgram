from django.urls import include, path

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('users/', include('users.urls')),

]

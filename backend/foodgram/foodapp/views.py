from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated


class FoodgramUserViewSet(UserViewSet):

    def get_queryset(self):
        return get_user_model().objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [AllowAny()]
        return [IsAuthenticated()]

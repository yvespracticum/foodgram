from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription
from .serializers import MySubscriptionsSerializer

User = get_user_model()


class FoodgramUserViewSet(UserViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [AllowAny()]
        return [IsAuthenticated()]


class SubscribeView(APIView):
    """Подписаться/отписаться на/от автора."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        """Подписаться на автора."""

        if not request:
            return Response({'error': 'request is None'}, status=400)
        if not request.user:
            return Response({'error': 'request.user is None'}, status=400)

        author = get_object_or_404(User, id=id)

        if request.user == author:
            return Response({"error": "Нельзя подписаться на самого себя."},
                            status=status.HTTP_400_BAD_REQUEST)

        if Subscription.objects.filter(follower=request.user,
                                       author=author).exists():
            return Response({
                "error": "Вы уже подписаны на этого автора."},
                status=status.HTTP_400_BAD_REQUEST)

        subscription = Subscription.objects.create(follower=request.user,
                                                   author=author)
        serializer = MySubscriptionsSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Отписаться от автора."""
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(follower=request.user,
                                                   author=author)

        if not subscription.exists():
            return Response({
                "error": "Вы не подписаны на этого автора."},
                status=status.HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MySubscriptionsView(APIView):
    """Получить список своих подписок."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get(self, request):
        """Получить список подписок."""
        subscriptions = Subscription.objects.filter(follower=request.user)
        serializer = MySubscriptionsSerializer(subscriptions, many=True,
                                               context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

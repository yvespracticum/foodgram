from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Recipe, Subscription

User = get_user_model()


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class MySubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор подписок текущего пользователя."""
    email = serializers.EmailField(source='author.email', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(
        source='author.first_name',
        read_only=True
    )
    last_name = serializers.CharField(
        source='author.last_name',
        read_only=True
    )
    avatar = serializers.ImageField(source='author.avatar', read_only=True)
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        """Количество рецептов автора."""
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj):
        """Получает список рецептов автора."""
        recipes = Recipe.objects.filter(author=obj.author)[
                  :3]
        return RecipeShortSerializer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли автор на текущего пользователя."""
        request = self.context.get('request')

        if not request:
            return 'no request'
        if not hasattr(request, 'user'):
            return 'request has no attr `user`'

        return Subscription.objects.filter(
            # follower=self.context.get('request').user,
            follower=request.user,
            author=obj.author
        ).exists()

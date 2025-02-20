import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from .constants import (DEFAULT_RECIPES_AMOUNT_AT_SUBSCRIPTIONS_PAGE,
                        INGREDIENT_MIN_AMOUNT, MIN_COOKING_TIME)
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, Tag)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для загрузки изображений в формате base64."""

    def to_internal_value(self, data):
        if data.startswith('data:image'):
            format_, imgstr = data.split(';base64,')
            ext = format_.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField()

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'avatar')

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли пользователь на автора."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(follower=request.user,
                                           author=obj).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""
    id = serializers.IntegerField(source='author.id', read_only=True)
    email = serializers.EmailField(source='author.email', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(source='author.first_name',
                                       read_only=True)
    last_name = serializers.CharField(source='author.last_name',
                                      read_only=True)
    avatar = serializers.ImageField(source='author.avatar', read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='author.recipes.count',
                                             read_only=True)

    class Meta:
        model = Subscription
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли пользователь на автора."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(follower=request.user,
                                           author=obj.author).exists()

    def get_recipes_count(self, obj):
        """Количество рецептов автора."""
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj):
        """Получает список рецептов автора с учетом `recipes_limit`."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)
        if recipes_limit and recipes_limit.isdigit():
            return RecipeShortSerializer(recipes[:int(recipes_limit)],
                                         many=True).data
        return RecipeShortSerializer(
            recipes[:DEFAULT_RECIPES_AMOUNT_AT_SUBSCRIPTIONS_PAGE],
            many=True).data


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватаров."""
    avatar = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        """Проверяет, что переданы корректные base64-данные."""
        try:
            format_, imgstr = value.split(';base64,')
            ext = format_.split('/')[-1]
            return base64.b64decode(imgstr), ext
        except Exception:
            raise serializers.ValidationError('Invalid base64 image format.')

    def update(self, instance, validated_data):
        """Обновляет аватар пользователя."""
        image_data, ext = validated_data['avatar']
        file_name = f'{uuid.uuid4()}.{ext}'
        instance.avatar.save(file_name, ContentFile(image_data), save=True)
        return instance


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    def to_internal_value(self, data):
        """Принимает id и конвертирует его в объект Tag."""
        if isinstance(data, int):
            return Tag.objects.get(id=data)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте с полем 'amount'."""
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта."""
    author = serializers.SerializerMethodField()
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = IngredientInRecipeSerializer(many=True,
                                               source='recipe_ingredients')
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart')

    def get_author(self, obj):
        """Возвращает автора в нужном формате."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            is_subscribed = False
        else:
            is_subscribed = Subscription.objects.filter(
                follower=request.user, author=obj.author).exists()
        return {
            'email': obj.author.email,
            'id': obj.author.id,
            'username': obj.author.username,
            'first_name': obj.author.first_name,
            'last_name': obj.author.last_name,
            'is_subscribed': is_subscribed,
            'avatar': obj.author.avatar.url if obj.author.avatar and hasattr(
                obj.author.avatar, 'url') else None}

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(recipe=obj,
                                           user=request.user).exists()

    def to_representation(self, instance):
        """Меняет отображение 'tags': при GET отдает объекты, а не id."""
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(instance.tags.all(),
                                               many=True).data
        return representation

    def validate_ingredients(self, value):
        """Проверка: список ингредиентов не пуст,
        без дублей и количество ингредиента не меньше минимума.
        """
        if not value:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым.')
        added_ingredients = set()
        for item in value:
            ingredient_id = item['id']
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    f'Ингредиента с id={ingredient_id} не существует.')
            amount = item['amount']
            if amount < INGREDIENT_MIN_AMOUNT:
                raise serializers.ValidationError(
                    f'Минимальное кол-во ингредиента: {INGREDIENT_MIN_AMOUNT}')
            if ingredient_id in added_ingredients:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.')
            added_ingredients.add(ingredient_id)
        return value

    def validate_tags(self, value):
        """Проверка: список тегов не пуст и без дублей."""
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один тег.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def validate_cooking_time(self, value):
        """Проверка: время приготовления >= 1."""
        if value < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f'Минимальное время приготовления: {MIN_COOKING_TIME}')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['author'] = request.user
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            ingredient_instance = Ingredient.objects.get(id=ingredient['id'])
            RecipeIngredient.objects.create(recipe=recipe,
                                            ingredient=ingredient_instance,
                                            amount=ingredient['amount'])
        return recipe

    def update(self, instance, validated_data):
        if 'tags' not in validated_data:
            raise serializers.ValidationError({'tags': 'Обязательное поле.'})
        else:
            instance.tags.set(validated_data.pop('tags'))
        if 'recipe_ingredients' not in validated_data:
            raise serializers.ValidationError({'tags': 'Обязательное поле.'})
        else:
            ingredients = validated_data.pop('recipe_ingredients')
            instance.recipe_ingredients.all().delete()
            for ingredient in ingredients:
                ingredient_instance = Ingredient.objects.get(
                    id=ingredient['id'])
                RecipeIngredient.objects.create(recipe=instance,
                                                ingredient=ingredient_instance,
                                                amount=ingredient['amount'])
        return super().update(instance, validated_data)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from .constants import (INGREDIENT_MIN_AMOUNT, INGREDIENT_NAME_MAX_LEN,
                        MEASUREMENT_UNIT_MAX_LEN, MIN_COOKING_TIME,
                        RECIPE_HASHCODE_MAX_LEN, RECIPE_NAME_MAX_LEN,
                        TAG_NAME_MAX_LEN, TAG_SLUG_MAX_LEN,
                        USER_FIRST_NAME_MAX_LEN, USER_LAST_NAME_MAX_LEN,
                        USER_USERNAME_MAX_LEN)


class FoodgramUser(AbstractUser):
    """Пользователь."""
    username = models.CharField(
        max_length=USER_USERNAME_MAX_LEN,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+\Z',
            message=r"Для поля 'username' не принимаются значения, "
                    r"не соответствующие регулярному выражению '^[\w.@+-]+\Z'",
            code='invalid_username')])
    avatar = models.ImageField(upload_to='avatars/')
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=USER_FIRST_NAME_MAX_LEN)
    last_name = models.CharField(max_length=USER_LAST_NAME_MAX_LEN)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def delete_avatar(self):
        """Удаляет файл аватара из базы данных."""
        if self.avatar:
            avatar_path = os.path.join(settings.MEDIA_ROOT, self.avatar.name)
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
            self.avatar = None
            self.save()

    def __str__(self):
        return f'{self.username}'


User = get_user_model()


class Ingredient(models.Model):
    """Ингредиент."""
    name = models.CharField(max_length=INGREDIENT_NAME_MAX_LEN, unique=True)
    measurement_unit = models.CharField(max_length=MEASUREMENT_UNIT_MAX_LEN)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}. Ед. изм.: {self.measurement_unit}.'


class Tag(models.Model):
    """Тег."""
    name = models.CharField(max_length=TAG_NAME_MAX_LEN, unique=True)
    slug = models.SlugField(max_length=TAG_SLUG_MAX_LEN, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепт."""
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes')
    name = models.CharField(max_length=RECIPE_NAME_MAX_LEN)
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField()
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         related_name='recipes')
    tags = models.ManyToManyField(Tag, related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    hashcode = models.CharField(max_length=RECIPE_HASHCODE_MAX_LEN,
                                unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def clean(self):
        """Проверка на:
            - наличие тегов
            - минимальное допустимое время приготовления рецепта
            - отсутствие повторяющихся ингредиентов
            - минимальное количество ингредиента
        при добавлении рецепта через админ панель.
        """
        if self.cooking_time < MIN_COOKING_TIME:
            raise ValidationError({
                'cooking_time': f'Минимальное время '
                                f'приготовления: {MIN_COOKING_TIME}'})
        if not self.pk and not self.tags.count():
            raise ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'})
        if not self.recipe_ingredients.exists():
            raise ValidationError(
                {'recipe_ingredients': 'Список ингредиентов '
                                       'не может быть пустым.'})

        ingredients_ids_set = set()
        for ingredient in self.recipe_ingredients.all():
            ingredient_id = ingredient.ingredient.id
            if ingredient_id in ingredients_ids_set:
                raise ValidationError(
                    {'recipe_ingredients': 'Ингредиенты не должны '
                                           'повторяться.'})
            if ingredient.amount < INGREDIENT_MIN_AMOUNT:
                raise ValidationError(
                    {'recipe_ingredients': f'Минимальное кол-во ингредиента: '
                                           f'{INGREDIENT_MIN_AMOUNT}'})
            ingredients_ids_set.add(ingredient_id)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Ингредиент в составе рецепта."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField()

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return (f'{self.ingredient}: {self.amount} '
                f'{self.ingredient.measurement_unit}')


class Subscription(models.Model):
    """Подписка."""
    follower = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='following')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='followers')

    class Meta:
        constraints = [models.UniqueConstraint(fields=('follower', 'author'),
                                               name='unique_subscription')]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.follower} подписан на {self.author}'


class Favorite(models.Model):
    """Избранное."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favoreted_by')

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'recipe'),
                                               name='unique_favorite')]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(models.Model):
    """Список покупок."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="shopping_cart")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name="in_shopping_cart")

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'recipe'),
                                               name='unique_shopping_cart')]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class FoodgramUser(AbstractUser):
    """Пользователь."""
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+\Z',
            message=r"Для поля 'username' не принимаются значения, "
                    r"не соответствующие регулярному выражению '^[\w.@+-]+\Z'",
            code='invalid_username')])
    avatar = models.ImageField(
        upload_to='avatars/',
        default='static/media/userpic-icon.2e3faa821bb5398be2c6.jpg',
        blank=True, null=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

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
    name = models.CharField(max_length=200, unique=True)
    measurement_unit = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}. Ед. изм.: {self.measurement_unit}.'


class Tag(models.Model):
    """Тег."""
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=20, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепт."""
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes')
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField()
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         related_name='recipes')
    tags = models.ManyToManyField(Tag, related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    hashcode = models.CharField(max_length=30, unique=True,
                                blank=True, null=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

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

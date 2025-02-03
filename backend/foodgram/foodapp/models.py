from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


class FoodgramUser(AbstractUser):
    """Пользователь."""
    username = models.CharField(max_length=150, unique=True)
    avatar = models.ImageField(upload_to='avatars/',
                               default='avatars/default_avatar.jpg',
                               blank=True, null=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f'{self.username}'


User = get_user_model()


class Ingredient(models.Model):
    """Ингредиент."""
    name = models.CharField(max_length=200, unique=True)
    unit = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.name}. Ед. изм.: {self.unit}.'


class Tag(models.Model):
    """Тег."""
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепт."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient',
        related_name='recipes'
    )
    tags = models.ManyToManyField(Tag, related_name='recipes')
    cooking_time_in_minutes = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Ингредиент в рецепте."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE

    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.FloatField()

    def __str__(self):
        return f'{self.ingredient}: {self.amount} {self.ingredient.unit}'


class Subscription(models.Model):
    """Подписка."""
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='followers'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.follower} подписан на {self.author}'

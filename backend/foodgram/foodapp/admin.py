from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError

from .constants import INGREDIENT_MIN_AMOUNT, MIN_COOKING_TIME
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

User = get_user_model()


class RecipeAdminForm(forms.ModelForm):
    """Проверка на:
        - минимальное допустимое время приготовления рецепта
        - наличие тегов
        - наличие ингредиентов
        - отсутствие повторяющихся ингредиентов
        - минимальное количество ингредиента
    при добавлении рецепта через админ панель.
    """

    class Meta:
        model = Recipe
        exclude = ('hashcode',)

    def clean(self):
        cleaned_data = super().clean()

        cooking_time = cleaned_data.get('cooking_time')
        if cooking_time is None or cooking_time < MIN_COOKING_TIME:
            raise ValidationError({
                'cooking_time': f'Минимальное время '
                                f'приготовления: {MIN_COOKING_TIME}'})

        tags = cleaned_data.get('tags')
        if not tags or not tags.exists():
            raise ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'})

        ingredients_list = self.data.getlist('recipe_ingredients')
        if not ingredients_list:
            raise ValidationError(
                {'recipe_ingredients': 'Список ингредиентов '
                                       'не может быть пустым.'})

        ingredients_ids_set = set()
        for ingredient_data in ingredients_list:
            ingredient_id, amount = map(int, ingredient_data.split(","))
            if ingredient_id in ingredients_ids_set:
                raise ValidationError({
                    'recipe_ingredients': 'Ингредиенты не должны повторяться.'
                })
            if amount < INGREDIENT_MIN_AMOUNT:
                raise ValidationError({
                    'recipe_ingredients': f'Минимальное кол-во ингредиента: '
                                          f'{INGREDIENT_MIN_AMOUNT}'})
            ingredients_ids_set.add(ingredient_id)

        return cleaned_data


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    """Админка для пользователей."""
    list_display = ('id', 'email', 'username', 'first_name', 'last_name')
    search_fields = ('email', 'username')
    ordering = ('id',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    """Отображение ингредиентов в рецепте."""
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""
    form = RecipeAdminForm
    list_display = ('id', 'name', 'author',
                    'get_tags', 'favorite_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = (RecipeIngredientInline,)

    @admin.display(description='Теги')
    def get_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])

    def favorite_count(self, obj):
        """Подсчёт добавлений в избранное."""
        return Favorite.objects.filter(recipe=obj).count()

    favorite_count.short_description = 'В избранном'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранного."""
    list_display = ('id', 'get_user_id', 'user', 'recipe', 'get_recipe_id')
    search_fields = ('user__username', 'recipe__name')

    @admin.display(description='User id')
    def get_user_id(self, obj):
        return obj.user.id

    @admin.display(description='Recipe id')
    def get_recipe_id(self, obj):
        return obj.recipe.id


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для списка покупок."""
    list_display = ('id', 'get_user_id', 'user', 'recipe', 'get_recipe_id')
    search_fields = ('user__username', 'recipe__name')

    @admin.display(description='User id')
    def get_user_id(self, obj):
        return obj.user.id

    @admin.display(description='Recipe id')
    def get_recipe_id(self, obj):
        return obj.recipe.id

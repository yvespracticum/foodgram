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
            raise ValidationError(
                {'cooking_time': (f'Минимальное время приготовления: '
                                  f'{MIN_COOKING_TIME}')})

        tags = cleaned_data.get('tags')
        if not tags or not tags.exists():
            raise ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'})

        if self.instance.pk:
            # Для существующего рецепта
            if not self.instance.recipe_ingredients.exists():
                raise ValidationError(
                    {'recipe_ingredients': 'Список ингредиентов '
                                           'не может быть пустым.'})

            ingredients_ids_set = set()
            for ri in self.instance.recipe_ingredients.all():
                ingredient_id = ri.ingredient.id
                if ingredient_id in ingredients_ids_set:
                    raise ValidationError(
                        {'recipe_ingredients': 'Ингредиенты не могут '
                                               'повторяться.'})
                if ri.amount < INGREDIENT_MIN_AMOUNT:
                    raise ValidationError(
                        {'recipe_ingredients': f'Минимальное кол-во '
                                               f'ингредиента '
                                               f'{INGREDIENT_MIN_AMOUNT}'})
                ingredients_ids_set.add(ingredient_id)

        return cleaned_data

    def clean_cooking_time(self):
        """Выделенная валидация для времени приготовления."""
        cooking_time = self.cleaned_data.get('cooking_time')
        if cooking_time and cooking_time < MIN_COOKING_TIME:
            raise ValidationError(
                f'Минимальное время приготовления: {MIN_COOKING_TIME}')
        return cooking_time


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


class RecipeIngredientInlineFormSet(forms.models.BaseInlineFormSet):
    """Формсет для ингредиентов рецепта с валидацией."""

    def clean(self):
        """Проверка валидности набора форм ингредиентов."""
        super().clean()

        # Проверка на наличие хотя бы одного ингредиента
        has_ingredients = any(
            form.cleaned_data and not form.cleaned_data.get('DELETE', False)
            for form in self.forms)
        if not has_ingredients:
            raise ValidationError('Добавьте хотя бы один ингредиент.')

        ingredients_ids = set()
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE', False):
                continue

            ingredient = form.cleaned_data.get('ingredient')
            if ingredient:
                if ingredient.id in ingredients_ids:
                    raise ValidationError('Ингредиенты не могут повторяться.')
                ingredients_ids.add(ingredient.id)

            amount = form.cleaned_data.get('amount')
            if amount and amount < INGREDIENT_MIN_AMOUNT:
                raise ValidationError(f'Минимальное количество ингредиента: '
                                      f'{INGREDIENT_MIN_AMOUNT}')


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн-форма для ингредиентов рецепта."""
    model = RecipeIngredient
    formset = RecipeIngredientInlineFormSet
    min_num = 1
    validate_min = True
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

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

User = get_user_model()


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

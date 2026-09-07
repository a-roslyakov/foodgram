from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


class IngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through


class TagInline(admin.TabularInline):
    model = Recipe.tags.through


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = ('name', 'image', 'text', 'cooking_time', 'favorite_count')
    readonly_fields = ('favorite_count',)
    list_display = ('name', 'author__username', 'favorite_count')
    list_filter = ('tags__name',)
    list_select_related = True
    search_fields = ['name', 'author_username']
    inlines = [
        IngredientInline,
        TagInline
    ]

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        """Сколько раз рецепт был добавлен в избранное."""
        return obj.favorites.all().count()


@admin.register(Ingredient)
class IngridientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    pass

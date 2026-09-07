import django_filters.rest_framework as filters

from recipes.models import Ingredient, Recipe


class AuthorTagsFavoritedInShoppingCartFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        field_name='is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        field_name='is_in_shopping_cart'
    )
    tags = filters.CharFilter(
        field_name='tags__slug',
        method='filter_tags',
        distinct=True
    )
    author = filters.NumberFilter(field_name='author__id', distinct=True)

    class Meta:
        model = Recipe
        fields = (
            'is_favorited',
            'is_in_shopping_cart',
            'author',
            'tags'
        )

    def filter_tags(self, queryset, name, value):
        slugs = self.request.query_params.getlist('tags')
        return queryset.filter(tags__slug__in=slugs)

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(shopping_carts__user=user)
        return queryset


class NameFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)

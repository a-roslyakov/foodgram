from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import AuthorTagsFavoritedInShoppingCartFilter, NameFilter
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)
from .paginations import CustomPagination
from .permissions import IsAuthorOnly
from .serializers import IngredientSerializer, RecipeSerializer, TagSerializer
from .utils import create_or_delete_user_recipe_relation


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = NameFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related(
        'tags', 'ingredients'
    ).select_related('author')
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    filterset_class = AuthorTagsFavoritedInShoppingCartFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request'] = self.request
        return context

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create', 'get_link']:
            permission_classes = [IsAuthenticatedOrReadOnly]
        else:
            permission_classes = [IsAuthorOnly]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['GET'],
        detail=True,
        url_path='get-link',
    )
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        base_url = request.build_absolute_uri('/')
        short_link = f'{base_url}s/{recipe.short_link}/'
        return Response(
            {
                'short-link': short_link
            }
        )

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        )

        lines = []
        for ingredient in ingredients:
            lines.append(
                f"{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) - "
                f"{ingredient['total_amount']}"
            )

        content = '\n'.join(lines)
        byte_content = content.encode('utf-8')
        file_buffer = BytesIO(byte_content)
        return FileResponse(
            file_buffer,
            as_attachment=True,
            filename=f'{user.username}_shopping_cart.txt',
        )

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        return create_or_delete_user_recipe_relation(
            request=request,
            recipe=recipe,
            model=ShoppingCart,
            model_name='список покупок'
        )

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        return create_or_delete_user_recipe_relation(
            request=request,
            recipe=recipe,
            model=Favorite,
            model_name='избранное'
        )

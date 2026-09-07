from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import AuthorTagsFavoritedInShoppingCartFilter, NameFilter
from .paginations import Pagination
from .permissions import IsAuthorOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeSerializer, SubscriptionsCreateSerializer,
                          SubscriptionsReadSerializer, TagSerializer,
                          UserReadSerializer)
from .utils import create_or_delete_user_recipe_relation
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


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
    pagination_class = Pagination
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
        ).annotate(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit'),
            total_amount=Sum('amount')
        ).values('name', 'measurement_unit', 'total_amount')

        lines = []
        for ingredient in ingredients:
            lines.append(
                f"{ingredient['name']} "
                f"({ingredient['measurement_unit']}) - "
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
        methods=['POST', 'DELETE'],  # Не понял про mapping.delete
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


class UserViewSet(DjoserViewSet):
    pagination_class = Pagination

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = UserReadSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['PUT', 'DELETE'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': 'Аватар не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AvatarSerializer(user, data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthorOnly]
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(subscribes__user=user).annotate(
            recipes_count=Count('recipes')
        )

        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionsReadSerializer(
                page,
                context={'request': request},
                many=True
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionsReadSerializer(
            subscriptions,
            context={'request': request},
            many=True
        )
        return Response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            serializer = SubscriptionsCreateSerializer(
                data={'author': author.id},
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'DELETE':
            if user.subscriptions.filter(
                author=author
            ).exists():
                Subscription.objects.filter(user=user, author=author).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'delete': 'Вы не подписаны на этого пользователя.'},
            status=status.HTTP_400_BAD_REQUEST
        )

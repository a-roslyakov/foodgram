import secrets

from .serializers import FavoriteSerializer, ShoppingCartSerializer
from recipes.constants import LENGTH_SHORT_LINK
from recipes.models import ShoppingCart
from rest_framework import status
from rest_framework.response import Response


def get_short_code():
    return secrets.token_urlsafe(LENGTH_SHORT_LINK)


def create_or_delete_user_recipe_relation(request, recipe, model, model_name):
    current_object = model.objects.filter(user=request.user, recipe=recipe)
    if request.method == 'DELETE':
        count, _ = current_object.delete()
        if count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': f'Этот рецепт не был добавлен в {model_name}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if request.method == 'POST':
        serializer_class = (
            ShoppingCartSerializer if model == ShoppingCart
            else FavoriteSerializer
        )
        serializer = serializer_class(
            data={'recipe': recipe.id},
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

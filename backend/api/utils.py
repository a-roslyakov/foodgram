import secrets

from rest_framework import status
from rest_framework.response import Response

from .serializers import FavoriteSerializer, ShoppingCartSerializer
from recipes.constants import LENGTH_SHORT_LINK
from recipes.models import ShoppingCart


def get_short_code():
    return secrets.token_urlsafe(LENGTH_SHORT_LINK)


def create_or_delete_user_recipe_relation(request, recipe, model, model_name):
    current_object = model.objects.filter(user=request.user, recipe=recipe)
    if current_object.exists() and request.method == 'DELETE':
        current_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        if request.method == 'DELETE':
            return Response(
                {'detail': f'Этот рецепт не был добавлен в {model_name}'},
                status=status.HTTP_400_BAD_REQUEST
            )
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

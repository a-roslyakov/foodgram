import secrets

from rest_framework import status
from rest_framework.response import Response

from .constants import LENGTH_SHORT_LINK


def get_short_code():
    return secrets.token_urlsafe(LENGTH_SHORT_LINK)


def set_tags_and_ingredients(recipe, tags, ingredients, update=False):
    from .models import RecipeIngredient

    recipe.tags.set(tags)

    if update:
        RecipeIngredient.objects.filter(recipe=recipe).delete()

    for ingredient in ingredients:
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient['id'],
            amount=ingredient['amount']
        )


def user_has_relation(request, model, recipe):
    if not request or not request.user.is_authenticated:
        return False
    return model.objects.filter(
        user=request.user, recipe=recipe
    ).exists()


def create_or_delete_user_recipe_relation(request, recipe, model, model_name):
    from .models import ShoppingCart
    from .serializers import (
        FavoriteSerializer,
        RecipeNameImageCookingTimeSerializer,
        ShoppingCartSerializer
    )

    current_object = model.objects.filter(user=request.user, recipe=recipe)

    if current_object.exists():
        if request.method == 'POST':
            return Response(
                {'detail': f'Этот рецепт уже добавлен в {model_name}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        current_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        if request.method == 'POST':
            serializer_class = (
                ShoppingCartSerializer if model == ShoppingCart
                else FavoriteSerializer
            )
            serializer = serializer_class(
                data={'recipe': recipe.id},
                context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                recipe_serializer = RecipeNameImageCookingTimeSerializer(
                    recipe
                )
                return Response(
                    recipe_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': f'Этот рецепт не был добавлен в {model_name}'},
            status=status.HTTP_400_BAD_REQUEST
        )

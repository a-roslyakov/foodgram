from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, validators

from users.serializers import UserReadSerializer
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)
from .utils import set_tags_and_ingredients, user_has_relation


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(
        required=True,
        many=True,
        write_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField(required=True)
    name = serializers.CharField(
        max_length=256,
        required=True,
        validators=[validators.UniqueValidator(
            queryset=Recipe.objects.all(),
            message='Это имя уже используется'
        )
        ]
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'image', 'name', 'text', 'cooking_time'
        )

    def to_representation(self, instance):
        """Переопределение сериализаторов для отображения."""
        data = super().to_representation(instance)

        data['ingredients'] = RecipeIngredientReadSerializer(
            instance.recipe_ingredient.all(),
            many=True
        ).data

        data['tags'] = TagSerializer(instance.tags.all(), many=True).data

        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)

        set_tags_and_ingredients(
            recipe=recipe,
            tags=tags,
            ingredients=ingredients
        )

        return recipe

    def update(self, instance, validated_data):
        try:
            tags = validated_data.pop('tags')
            ingredients = validated_data.pop('ingredients')
        except KeyError:
            raise serializers.ValidationError

        instance = super().update(instance, validated_data)

        set_tags_and_ingredients(
            recipe=instance,
            tags=tags,
            ingredients=ingredients,
            update=True
        )

        return instance

    def validate(self, attrs):
        tags = attrs.get('tags')
        ingredients = attrs.get('ingredients')
        image = attrs.get('image')

        fields = {
            'Теги': tags,
            'Ингредиенты': ingredients,
            'Фото': image
        }

        for field_name, value in fields.items():
            if not value:
                raise serializers.ValidationError(
                    f'{field_name} обязательны и не может быть пустым.'
                )

        return attrs

    def validate_tags(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги должны быть уникальными.')
        return value

    def validate_ingredients(self, value):
        ingredient_ids = [ingredient['id'] for ingredient in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return value

    def get_is_favorited(self, obj):
        request = self.context['request']
        return user_has_relation(request, Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return user_has_relation(request, ShoppingCart, obj)


class UserRecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для связей пользователь-рецепт."""

    class Meta:
        abstract = True

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return self.Meta.model.objects.create(**validated_data)


class ShoppingCartSerializer(UserRecipeRelationSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('recipe',)


class FavoriteSerializer(UserRecipeRelationSerializer):
    class Meta:
        model = Favorite
        fields = ('recipe',)


class RecipeNameImageCookingTimeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')

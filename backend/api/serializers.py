from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import (
    MaxValueValidator, MinValueValidator, RegexValidator
)
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, validators

from recipes.constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_QUANTITY_FOR_RECIPE_MODEL,
    USER_PERSONAL_DATA_LENTH,
    VALIDATE_VALUE_MAX,
    VALIDATE_VALUE_MIN
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class UserRecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для связей пользователь-рецепт."""

    class Meta:
        abstract = True

    def validate(self, attrs):
        request = self.context['request']
        if self.Meta.model.objects.filter(
            user=request.user, recipe=attrs['recipe']
        ).exists():
            raise serializers.ValidationError()
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return self.Meta.model.objects.create(**validated_data)

    def to_representation(self, instance):
        recipe = instance.recipe
        return RecipeNameImageCookingTimeSerializer(recipe).data


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


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        ]
        read_only_fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        max_length=MAX_LENGTH_EMAIL,
        required=True,
        validators=[validators.UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        max_length=USER_PERSONAL_DATA_LENTH,
        required=True,
        validators=[
            validators.UniqueValidator(queryset=User.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=(
                    'Имя пользователя может содержать только буквы, цифры и'
                    'символы: @.+-_'
                )
            )
        ]
    )
    first_name = serializers.CharField(
        max_length=USER_PERSONAL_DATA_LENTH,
        required=True
    )
    last_name = serializers.CharField(
        max_length=USER_PERSONAL_DATA_LENTH,
        required=True
    )
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name',),
            last_name=validated_data.get('last_name',)
        )
        return user


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    current_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return value

    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.password = new_password
        user.save()


class SubscriptionsCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('author',)

    def validate(self, attrs):
        request = self.context['request']
        author = attrs['author']
        if author == request.user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        elif request.user.subscriptions.filter(
            author=author
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на пользователя'
            )

        return attrs

    def to_representation(self, instance):
        return SubscriptionsReadSerializer(
            self.context['author'],
            context=self.context
        ).data

    # Не сообразил как выполнить замечание с аннотированием во view и передачи
    # именно этого объекта в сериализатор для subsctibe..


class SubscriptionsReadSerializer(UserReadSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField()

    class Meta(UserReadSerializer.Meta):
        fields = list(UserReadSerializer.Meta.fields) + [
            'recipes',
            'recipes_count'
        ]

    def get_recipes(self, obj):
        recipes_author = obj.recipes.all()
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes_author = recipes_author[:int(recipes_limit)]
            except (ValueError, TypeError):
                pass

        serializer = RecipeNameImageCookingTimeSerializer(
            recipes_author,
            many=True
        )
        return serializer.data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='ingredient.id',
        read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('amount',)


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(VALIDATE_VALUE_MIN),
            MaxValueValidator(VALIDATE_VALUE_MAX)
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserReadSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredient', read_only=True, many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'image', 'name', 'text', 'cooking_time'
        )
        read_only_fields = ('image', 'name', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context['request']
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        if not request or not request.user.is_authenticated:
            return False
        return obj.shopping_carts.filter(user=request.user).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
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
        max_length=MAX_LENGTH_QUANTITY_FOR_RECIPE_MODEL,
        required=True,
        validators=[validators.UniqueValidator(
            queryset=Recipe.objects.all(),
            message='Это имя уже используется'
        )
        ]
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'image', 'name', 'text',
            'cooking_time'
        )

    @staticmethod
    def set_tags_and_ingredients(recipe, tags, ingredients):

        recipe.tags.set(tags)

        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)

        RecipeCreateSerializer.set_tags_and_ingredients(
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
            raise serializers.ValidationError()

        instance = super().update(instance, validated_data)

        RecipeIngredient.objects.filter(recipe=instance).delete()

        RecipeCreateSerializer.set_tags_and_ingredients(
            recipe=instance,
            tags=tags,
            ingredients=ingredients,
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

        ingredient_ids = [ingredient['id'] for ingredient in ingredients]

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными.')
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )

        return attrs

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Subscription

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )
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
        max_length=254,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=(
                    'Имя пользователя может содержать только буквы, цифры и'
                    'символы: @.+-_'
                )
            )
        ]
    )
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
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

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Subscription.objects.create(**validated_data)


class SubscriptionsReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        recipes_author = obj.recipes.all()
        request = self.context['request']
        from recipes.serializers import RecipeNameImageCookingTimeSerializer
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'recipes_limit': 'Количество рецептов должно быть числом!'
                })
            else:
                if recipes_limit > 0:
                    recipes_author = recipes_author[:recipes_limit]

        serializer = RecipeNameImageCookingTimeSerializer(
            recipes_author,
            many=True
        )
        return serializer.data

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserViewSet
from recipes.paginations import CustomPagination
from recipes.permissions import IsAuthorOnly
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Subscription
from .serializers import (AvatarSerializer, SubscriptionsCreateSerializer,
                          SubscriptionsReadSerializer, UserReadSerializer)

User = get_user_model()


class UserViewSet(DjoserViewSet):
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = User.objects.all()
        return queryset

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
        subscriptions = User.objects.filter(subscribes__user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionsReadSerializer(
                page,
                context={'request': request},
                many=True
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionsReadSerializer(
            page,
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
        user = self.request.user
        author = get_object_or_404(User, pk=id)

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            if request.method == 'POST':
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.filter(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            if request.method == 'POST':
                serializer = SubscriptionsCreateSerializer(
                    data={'author': author.id},
                    context={'request': request}
                )
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    subscription_serializer = SubscriptionsReadSerializer(
                        author,
                        context={'request': request}
                    )
                    return Response(
                        subscription_serializer.data,
                        status=status.HTTP_201_CREATED
                    )
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'delete': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

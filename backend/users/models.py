from django.contrib.auth.models import AbstractUser
from django.db import models

from recipes.constants import NAME_MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField('Электронная почта', unique=True)
    avatar = models.ImageField('Фото профиля', default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username', 'password')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:NAME_MAX_LENGTH]


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='subscribes',
        verbose_name='Подписка'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_subscription_to_author'
            )
        ]

    def __str__(self):
        return (
            f'Подписка пользователя {self.user.username} на'
            f'автора {self.author.username}'
        )

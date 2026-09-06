from django.contrib.auth.models import AbstractUser
from django.db import models
from recipes.constants import NAME_MAX_LENGTH


class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to='users_avatars/', blank=True)
    email = models.EmailField('Электронная почта', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username', 'password')

    def __str__(self):
        return self.username[:NAME_MAX_LENGTH]


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='subscribes'
    )

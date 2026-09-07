from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'username', 'first_name', 'last_name', 'subscriptors_count',
        'recipes_count'
    )
    list_filter = ('email', 'username')
    search_fields = ['email', 'username']

    @admin.display(description='Количество подписчиков')
    def subscriptors_count(self, obj):
        return obj.subscriptions.count()

    @admin.display(description='Количество рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()

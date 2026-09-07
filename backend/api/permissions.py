from rest_framework.permissions import IsAuthenticated


class IsAuthorOnly(IsAuthenticated):
    """Доступ только автору."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.author

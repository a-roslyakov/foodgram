from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'users'

users_router_v1 = DefaultRouter()
users_router_v1.register('users', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(users_router_v1.urls)),
]

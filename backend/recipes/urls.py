from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

recipes_router_v1 = DefaultRouter()
recipes_router_v1.register(
    'recipes', views.RecipeViewSet, basename='recipes'
)
recipes_router_v1.register('tags', views.TagViewSet, basename='tags')
recipes_router_v1.register(
    'ingredients', views.IngredientViewSet, basename='ingredients'
)

urlpatterns = [
    path('', include(recipes_router_v1.urls))
]

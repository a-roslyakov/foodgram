from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import NAME_MAX_LENGTH
from .utils import get_short_code

User = get_user_model()


class NameBaseModel(models.Model):
    """Базовая модель с полем имени."""
    name = models.CharField('Название', max_length=256, unique=True)

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name[:NAME_MAX_LENGTH]


class Tag(NameBaseModel):
    slug = models.SlugField('Слаг')

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(NameBaseModel):
    measurement_unit = models.CharField('Единица измерения', max_length=256)

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class Recipe(NameBaseModel):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag)
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления(в минутах)',
        validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )
    short_link = models.CharField(
        'Короткая ссылка',
        unique=True,
    )

    class Meta(NameBaseModel.Meta):
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        """Получение уникальной короткой ссылки."""
        if not self.short_link:
            code = get_short_code()

            while Recipe.objects.filter(
                short_link=code,
            ).exists():
                code = get_short_code()

            self.short_link = code

        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент'
    )
    amount = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )

    class Meta:
        default_related_name = 'recipe_ingredient'


class UserRecipeBaseModel(models.Model):
    """Базовая модель с полями пользователя и рецепта."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True


class ShoppingCart(UserRecipeBaseModel):

    class Meta:
        default_related_name = 'shopping_carts'
        verbose_name = 'Список покупок пользователей'
        verbose_name_plural = 'Списки покупок пользователей'

    def __str__(self):
        return f'Рецепт{self.recipe} в списке покупок пользователя {self.user}'


class Favorite(UserRecipeBaseModel):

    class Meta:
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'Рецепт{self.recipe} в избранном пользователя {self.user}'

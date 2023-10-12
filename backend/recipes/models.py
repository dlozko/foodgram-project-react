from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    """Модель тегов."""
    name = models.CharField('Название тега',
                            max_length=200,
                            unique=True)
    color = models.CharField('Цвет тега',
                             max_length=7,
                             unique=True,
                             default='#')
    slug = models.SlugField('Slug',
                            max_length=200,
                            unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField('Название ингредиента',
                            max_length=200,)
    measurement_unit = models.CharField('Единица измерения',
                                        max_length=200,)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    '''Модель рецепта'''
    name = models.CharField('Название рецепта',
                            max_length=200)
    image = models.ImageField('Картинка',
                              upload_to='recipes/',
                              blank=True)
    text = models.TextField('Описание рецепта',
                            max_length=1000)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор',
                               related_name='recipes')
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(
                1, 'Время приготовления должно быть от 1 минуты')]
    )
    pub_date = models.DateTimeField(
        'Дата и время публикации рецепта',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """ Модель для связи ингредиента и рецепта. """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'

    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                1, 'Минимальное количество ингредиентов 1'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
#        constraints = [
#            models.UniqueConstraint(
#                fields=['recipe', 'ingredient'],
#                name='recipe_ingredient_unique')]


class Favorite(models.Model):
    '''Модель для избранных рецептов'''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_favorite'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user.username} добавил {self.recipe.name} в избраннное'


class ShoppingList(models.Model):
    '''Модель корзины покупок'''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Рецепт'
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_cart'
            )
        ]
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'

    def __str__(self):
        return (f'{self.user.username} добавил'
                f'{self.recipe.name} в корзину покупок')

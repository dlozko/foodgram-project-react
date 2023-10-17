from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.serializers import (ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        ValidationError, CharField,
                                        IntegerField)
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.fields import SerializerMethodField

from .fields import Base64ImageField
from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                            Favorite, ShoppingList)
from users.models import Follow, User


class UserNewSerializer(UserCreateSerializer):
    """Сериализатор для регистрации новых пользователей."""
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class UserSerializer(UserSerializer):
    """ Сериализатор для модели User."""
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user is None or user.is_anonymous:
            return False
        return Follow.objects.filter(user=user,
                                     author=obj).exists()


class RecipeFavoriteSerializer(ModelSerializer):
    """ Сериализатор ответа при добавлении рецепта в избранное."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscribeListSerializer(UserSerializer):
    """ Сериализатор для получения подписок."""
    is_subscribed = SerializerMethodField(read_only=True)
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes',
                  'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = None
        recipes = obj.recipes.all()
        if request:
            limit = request.GET.get('recipes_limit')
        if limit:
            recipes = obj.recipes.all()[:int(limit)]
        serializer = RecipeFavoriteSerializer(recipes, many=True,
                                              context={'request': request})
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionSerializer(ModelSerializer):
    """ Сериализатор для подписки, отписки."""
    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [UniqueTogetherValidator(
            queryset=Follow.objects.all(),
            fields=('user', 'author'),
            message='Подписка уже существует')
        ]

    def validate(self, data):
        request = self.context.get('request').user
        if data['author'] == request:
            raise ValidationError(
                'Нельзя подписываться на самого себя')
        return data

    def to_representation(self, instance):
        return UserSubscribeListSerializer(instance.author,
                                           context={'request':
                                                    self.context.get('request')
                                                    }).data


class IngredientSerializer(ModelSerializer):
    """ Сериализатор ингредиента."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerialiser(ModelSerializer):
    """ Сериализатор тега."""
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(ModelSerializer):
    """ Сериализатор получения ингредиента в рецепте."""
    id = IntegerField(read_only=True, source='ingredient.id')
    name = CharField(read_only=True, source='ingredient.name')
    measurement_unit = CharField(
        read_only=True, source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAddSerializer(ModelSerializer):
    """ Сериализатор добавления ингредиента в рецепте."""
    id = IntegerField()
    amount = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(ModelSerializer):
    """ Сериализатор получения информации о рецепте."""
    tags = TagSerialiser(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(read_only=True, many=True,
                                             source='recipe_ingredients')
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'author', 'tags', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingList.objects.filter(
            recipe=obj, user=request.user
        ).exists()


class RecipeCreateSerializer(ModelSerializer):
    """ Сериализатор добавления, обновления рецепта."""
    ingredients = IngredientAddSerializer(many=True,
                                          source='recipe_ingredients')
    tags = PrimaryKeyRelatedField(many=True,
                                  queryset=Tag.objects.all())
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('name', 'tags', 'image',
                  'ingredients', 'text', 'cooking_time')

    def validate(self, data):
        ingredients_list = []
        for ingredient in data.get('recipe_ingredients'):
            if int(ingredient.get('amount')) < 1:
                raise ValidationError(
                    'Количество ингредиента должно быть больше 0')
            if ingredient.get('id') in ingredients_list:
                raise ValidationError(
                    'Есть одинаковые ингредиенты!')
            ingredients_list.append(ingredient.get('id'))
        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredient_list = []
        for ingredient_data in ingredients:
            ingredient_list.append(
                RecipeIngredient(
                    ingredient_id=ingredient_data.get('id'),
                    amount=ingredient_data.get('amount'),
                    recipe=recipe,
                )
            )
        RecipeIngredient.objects.bulk_create(ingredient_list)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(author=self.context.get('request').user,
                                       **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        self.create_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context={'request': self.context.get('request')}).data


class FavoriteSerializer(ModelSerializer):
    """ Сериализатор избранных рецептов."""
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [UniqueTogetherValidator(
            queryset=Favorite.objects.all(),
            fields=('user', 'recipe'),
            message='Рецепт уже в избранном')]

    def to_representation(self, instance):
        return RecipeFavoriteSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}).data


class ShoppingListSerializer(ModelSerializer):
    """ Сериализатор покупки ингредиентов."""
    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в корзину'
            )
        ]

    def to_representation(self, instance):
        return RecipeFavoriteSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}).data
    
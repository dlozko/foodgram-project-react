from django.db import transaction
import base64
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.serializers import (ModelSerializer,
                                        SerializerMethodField,
                                        PrimaryKeyRelatedField,
                                        ValidationError, CharField,
                                        IntegerField, ImageField)                                       
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.fields import SerializerMethodField
from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                        Favorite, ShoppingList, )
from users.models import User, Follow


class UserNewSerializer(UserCreateSerializer):
    '''Сериализатор для регистрации новых пользователей.'''
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class UserSerializer(UserSerializer):
    '''Сериализатор для модели User.'''
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
    '''Сериализатор ответа при добавлении рецепта в избранное'''
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscribeListSerializer(UserSerializer):
    """ Сериализатор для получения подписок """
    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes',
                  'recipes_count')
        read_only_fields = ('email', 'username', 'first_name',
                            'last_name', 'is_subscribed',
                            'recipes', 'recipes_count')
    
    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = None
        recipes = obj.recipes.all()
        if request:
            limit = request.GET.get('recipes_limit')
        if limit:
            recipes = obj.recipes.all()[:int(limit)]
        serializer = RecipeFavoriteSerializer(recipes, many=True,
                                     context={'request':request})
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionSerializer(ModelSerializer):
    class Meta:
        model = Follow
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Подписка уже существует'
            )
        ]

    def validate(self, data):
        request = self.context.get('request').user
        if data['author'] == request:
            raise ValidationError(
                'Нельзя подписаться на самого себя')
        return data

    def to_representation(self, instance):
        return UserSubscribeListSerializer(instance.author,
            context={'request': self.context.get('request')
        }).data


class TagSerialiser(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(ModelSerializer):
    id = IntegerField(read_only=True, source='ingredient.id')
    name = CharField(read_only=True, source='ingredient.name')
    measurement_unit = CharField(
        read_only=True, source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAddSerializer(ModelSerializer):
    id = IntegerField()
    amount = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')  
            ext = format.split('/')[-1]  
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerialiser(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, read_only=True,
                                          source='recipeingredients')
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
        return (request and request.user.is_authenticated
                and Favorite.objects.filter(
                    user=request.user, recipe=obj
                ).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and ShoppingList.objects.filter(
                    user=request.user, recipe=obj
                ).exists())


class RecipeCreateSerializer(ModelSerializer):
    ingredients = IngredientAddSerializer(
        many=True, source='recipeingredients')
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('name', 'tags', 'image',
                  'ingredients', 'text', 'cooking_time')

    def validate(self, data):
        ingredients_list = []
        for ingredient in data.get('recipeingredients'):
            if int(ingredient.get('amount')) < 1:
                raise ValidationError(
                    'Количество ингредиента должно быть больше 0')
            ingredients_list.append(ingredient.get('id'))
         #   if ingredient.get('id') in ingredients_list:
         #       raise ValidationError(
         #           'Есть одинаковые ингредиенты!')
         #   ingredients_list.append(ingredient.get('id'))
        if len(set(ingredients_list)) != len(ingredients_list):
            raise ValidationError(
                'Есть одинаковые ингредиенты'
            )
        return data


    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredient_liist = []
        for ingredient_data in ingredients:
            current_ingredient = get_object_or_404(Ingredient, id=ingredient_data.get('id'))
            ingredient_liist.append(
                RecipeIngredient(
                    ingredient=current_ingredient,
                    amount=ingredient_data.get('amount'),
                    recipe=recipe,
                )
            )
        RecipeIngredient.objects.bulk_create(ingredient_liist)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('recipeingredients')
        recipe = Recipe.objects.create(author=self.context.get('request').user,
                                       **validated_data)
        recipe.tags.set(validated_data.pop('tags'))
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipeingredients')
        instance.tags.clear()
        instance.tags.set(validated_data.pop('tags'))
        RecipeIngredient.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        self.create_ingredients(instance, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance,
            context={'request': self.context.get('request')
            }).data


class FavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное'
            )
        ]

    def to_representation(self, instance):
        return RecipeFavoriteSerializer(
            instance.recipe,
            context={'request': self.context.get('request')
        }).data


class ShoppingListSerializer(ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = '__all__'
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
            context={'request': self.context.get('request')
        }).data

from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.serializers import (ModelSerializer,
                                        SerializerMethodField,
                                        PrimaryKeyRelatedField,
                                        ValidationError, CharField,
                                        IntegerField)                                       
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.fields import SerializerMethodField

from api.utils import Base64ImageField
from app.models import (Tag, Ingredient, Recipe, IngredientRecipe,
                        Favorities, ShoppingList, )
from users.models import User, Follow


class UserNewSerializer(UserCreateSerializer):
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
        return Follow.objects.filter(
            user=user,
            author=obj
        ).exists()


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
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        return RecipeFavoriteSerializer(recipes, many=True,
                                     context={'request':request}).data


    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionSerializer(ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
            queryset=Follow.objects.all(),
            fields=('user', 'author'),
            message='Вы уже подписаны на этого пользователя'
            )
        ]
    
    def validate(self, data):
        request = self.context.get('request')
        if data['author'] == data['user']:
            raise ValidationError(
                'Нельзя подписываться на себя!'
            )
        return data



class TagSerialiser(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug'
        )


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientRecipeSerializer(ModelSerializer):
    id = IntegerField(read_only=True, source='ingredient.id')
    name = CharField(read_only=True, source='ingredient.name')
    measurement_unit = CharField(
        read_only=True, source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAddSerializer(ModelSerializer):
    id = IntegerField()
    amount = IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerialiser(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(many=True, read_only=True,
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
                and Favorities.objects.filter(
                    user=request.user, recipe=obj
                )).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and ShoppingList.objects.filter(
                    user=request.user, recipe=obj
                )).exists()


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
        tags_list = []
        for ingredient in data.get('recipeingredients'):
            tags_list.append(ingredient.get('id'))
        if len(set(tags_list)) != len(tags_list):
            raise ValidationError(
                'Вы пытаетесь добавить в рецепт два одинаковых ингредиента'
            )
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        ingredients = validated_data.pop('recipeingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(Ingredient, id=ingredient.get('id'))
            amount = ingredient.get('amount')
            IngredientRecipe.objects.create(recipe=recipe, ingredient=current_ingredient, amount=amount)
        return recipe

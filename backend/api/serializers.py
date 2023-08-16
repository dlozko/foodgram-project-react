from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.fields import SerializerMethodField

from app.models import Ingredient, Recipe, Tag
from users.models import User, Subscription


class UserSignUpSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class UserGetSerializer(UserSerializer):
    '''Сериалайзер для модели User.'''
    is_subscribed = SerializerMethodField(read_only=True)
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')
    
    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user is None or user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user,
            author=obj
        ).exists()


class RecipeSmallSerializer(serializers.ModelSerializer):
    '''Сериализатор ответа при добавлении рецепта в избранное'''
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
    

class UserSubscribeRepresentSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name',
                            'is_subscribed', 'recipes', 'recipes_count')
    
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and Subscription.objects.filter(
                    user=request.user, author=obj
                ).exists())
    
    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = obj.recipes.all()[:int('recipes_limit')]
        return RecipeSmallSerializer(recipes, many=True).data


    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
            queryset=Subscription.objects.all(),
            fields=('user', 'author'),
            message='Вы уже подписаны на этого пользователя'
            )
        ]
    
    def validate(self, data):
        request = self.context.get('request')
        if data['author'] == data['user']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return data



class TagSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
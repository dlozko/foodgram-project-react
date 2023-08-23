from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, mixins
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import RecipeFilter, FilterIngredient
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (FavoriteSerializer , IngredientSerializer,
                          TagSerialiser, UserSubscribeListSerializer,
                          SubscriptionSerializer, ShoppingListSerializer,
                          RecipeCreateSerializer, RecipeReadSerializer)
from app.models import Ingredient, Tag, Recipe, Favorities, ShoppingList
from users.models import Follow, User


class UserSubscribeView(APIView):
    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if not Follow.objects.filter(user=request.user, author=author).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.get(user=request.user.id, author=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscriptionsViewSet(mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    serializer_class = UserSubscribeListSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения ингердиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = FilterIngredient
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny, )
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': request.user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Favorities.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'У вас нет этого рецепта в избранном'},
                    status=status.HTTP_404_NOT_FOUND
                )
            Favorities.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(
            detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ]
    )
    def shopping_list(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = ShoppingListSerializer(
                data={'user': request.user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not ShoppingList.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'У вас нет этого рецепта в корзине'},
                    status=status.HTTP_404_NOT_FOUND
                )
            ShoppingList.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
from django.shortcuts import get_object_or_404, HttpResponse
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorAdminOrReadOnly
from .serializers import (
    FavoriteSerializer, IngredientSerializer,
    RecipeCreateSerializer, RecipeReadSerializer,
    ShoppingListSerializer, SubscriptionSerializer,
    TagSerialiser, UserSubscribeListSerializer)
from .mixins import CreateDeleteMixin
from recipes.models import (Ingredient, Tag, Recipe, Favorite, ShoppingList,
                            RecipeIngredient)
from users.models import Follow, User


class UserSubscribeView(CreateDeleteMixin, APIView):
    """ Вью добавления, удаления подписки на пользователя."""

    def post(self, request, user_id):
        return self.create_object(
            request, get_object_or_404(User, id=user_id),
            SubscriptionSerializer, SubscriptionSerializer.Meta.fields
        )

    def delete(self, request, user_id):
        return self.delete_object(
            request, Follow, get_object_or_404(User, id=user_id),
            SubscriptionSerializer.Meta.fields
        )


class UserSubscriptionsViewSet(mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    """ Вьюсет получения списка подписок на пользователя."""
    serializer_class = UserSubscribeListSerializer

    def get_queryset(self):
        return User.objects.filter(followings__user=self.request.user)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет получения ингердиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет получения тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(CreateDeleteMixin, viewsets.ModelViewSet):
    """ Вьюсет работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.create_object(request, recipe, FavoriteSerializer,
                                      FavoriteSerializer.Meta.fields)
        return self.delete_object(request, Favorite, recipe,
                                  FavoriteSerializer.Meta.fields)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.create_object(request, recipe, ShoppingListSerializer,
                                      ShoppingListSerializer.Meta.fields)
        return self.delete_object(request, ShoppingList, recipe,
                                  ShoppingListSerializer.Meta.fields)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated, ])
    def download_shopping_cart(self, request):
        ingredient_lst = RecipeIngredient.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_lst = ['Список покупок:\n']
        for ingredient in ingredient_lst:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_lst.append(f'\n{name} - {amount}, {unit}')
        response = HttpResponse(shopping_lst, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"')
        return response

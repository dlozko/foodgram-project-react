from django.shortcuts import get_object_or_404, HttpResponse
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorAdminOrReadOnly
from .serializers import (
    FavoriteSerializer, IngredientSerializer,
    RecipeCreateSerializer, RecipeReadSerializer,
    ShoppingListSerializer, SubscriptionSerializer,
    TagSerialiser, UserSubscribeListSerializer)
from recipes.models import (Ingredient, Tag, Recipe, Favorite, ShoppingList,
                            RecipeIngredient)
from users.models import Follow, User


class UserSubscribeView(APIView):
    """ Вью добавления, удаления подписки на пользователя."""

    def post(self, request, user_id):
        return self.toggle_subscription(request, user_id, add=True)

    def delete(self, request, user_id):
        return self.toggle_subscription(request, user_id, add=False)

    def toggle_subscription(self, request, user_id, add=True):
        author = get_object_or_404(User, id=user_id)
        filter_params = {'user': request.user, 'author': author}

        if add:
            serializer = SubscriptionSerializer(data=filter_params,
                                                context={'request': request})
        else:
            serializer = SubscriptionSerializer(data=filter_params)

        if add and not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        elif not add and not Follow.objects.filter(**filter_params).exists():
            return Response({'errors': 'Вы не подписаны на этого пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)

        if add:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            Follow.objects.get(**filter_params).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


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
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет получения тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny, )
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ Вьюсет работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorAdminOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
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
            return self.create_object(request, recipe, FavoriteSerializer)
        return self.delete_object(request, Favorite, recipe)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.create_object(request, recipe, ShoppingListSerializer)
        return self.delete_object(request, ShoppingList, recipe)

    def create_object(self, request, instance, serializer_name):
        """ Функция добавления рецептов в избранное и корзину."""
        serializer = serializer_name(data={'user': request.user.id,
                                           'recipe': instance.id, },
                                     context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_object(self, request, model_name, instance):
        """ Функция удаления рецептов из избранного и корзины."""
        if not model_name.objects.filter(user=request.user,
                                         recipe=instance).exists():
            return Response(
                {'errors': 'Нет такого рецепта'},
                status=status.HTTP_404_BAD_REQUEST)
        model_name.objects.filter(user=request.user, recipe=instance).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

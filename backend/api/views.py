from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, mixins
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (IngredientSerializer, TagSerialiser,
                             UserSubscribeListSerializer,
                             SubscriptionSerializer,
                             RecipeCreateSerializer,
                             RecipeReadSerializer)
from app.models import Ingredient, Tag, Recipe
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
    filterset_class = IngredientFilter
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
    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from api.serializers import (IngredientSerializer, TagSerialiser,
                             UserSubscribeRepresentSerializer,
                             UserSubscribeSerializer)
from app.models import Ingredient, Tag
from users.models import Subscription, User


class UserSubscribeView(APIView):
    def post(self, request, user_id):
        user = get_object_or_404(User, username=request.user)
        author = get_object_or_404(User, id=user_id)
        serializer = UserSubscribeSerializer(
            data={'user': user.id, 'author': user_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = UserSubscribeRepresentSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def delete(self, request, user_id):
        user = get_object_or_404(User, username=request.user)
        author = get_object_or_404(User, id=user_id)
        if not Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.get(user=user.id, author=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения ингердиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (SearchFilter, )
    search_fields = ('^name', )
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny, )
    pagination_class = None

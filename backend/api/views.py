from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from api.serializers import IngredientSerializer, TagSerialiser
from app.models import Ingredient, Tag


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения ингердиентов."""
    queryset = Ingredient.objects.all()
    #serializer_class = IngredientSerializer
    #permission_classes = (AllowAny, )
   # filter_backends = (SearchFilter, )
    #search_fields = ('^name', )
    #Spagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny, )
    pagination_class = None

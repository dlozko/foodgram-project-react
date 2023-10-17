from rest_framework import status
from rest_framework.response import Response


class CreateDeleteMixin:

    def create_object(self, request, instance, serializer_name, fields):
        """ Функция добавления рецептов в избранное и корзину."""
        serializer = serializer_name(data={fields[0]: request.user.id,
                                           fields[1]: instance.id, },
                                     context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_object(self, request, model_name, instance, fields):
        """ Функция удаления рецептов из избранного и корзины."""
        data = {
            fields[0]: request.user,
            fields[1]: instance
        }
        if not model_name.objects.filter(**data).exists():
            return Response(
                {'errors': 'Запись еще не существует'},
                status=status.HTTP_400_BAD_REQUEST)
        model_name.objects.filter(**data).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

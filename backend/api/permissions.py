from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorAdminOrReadOnly(BasePermission):
    """Права доступа автора и администратора"""
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                or request.method in SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        return (request.user.is_staff or obj.author == request.user
                or request.method in SAFE_METHODS
                or request.user.is_superuser)

from rest_framework.permissions import BasePermission


class IsSuperuser(BasePermission):
    message = "Operazione riservata ai superutenti."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )

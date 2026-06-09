from rest_framework.permissions import BasePermission

class IsResponsabile(BasePermission):
    message = "Operazione riservata ai responsabili amministrativi."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_responsabile
        )


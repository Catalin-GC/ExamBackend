from rest_framework.permissions import BasePermission


class IsReferente(BasePermission):
    message = "Solo i referenti possono fare questa operazione."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_referente

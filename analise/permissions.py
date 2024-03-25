from rest_framework.permissions import BasePermission

class IsAdminOrStaff(BasePermission):
    """
    Permite o acesso apenas para usuários admin ou staff.
    """

    def has_permission(self, request, view):
        # Permite acesso se o usuário for admin ou staff
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))

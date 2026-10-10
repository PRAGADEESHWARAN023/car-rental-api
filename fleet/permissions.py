from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User


def is_fleet_staff(user):
    return bool(
        user
        and user.is_authenticated
        and user.role in (User.Role.STAFF, User.Role.ADMIN)
    )


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_fleet_staff(request.user)

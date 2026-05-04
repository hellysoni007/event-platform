from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import UserRole
from core.error_codes import ErrorCodes


class IsFacilitatorOrReadOnly(BasePermission):
    message = ErrorCodes.FORBIDDEN_ROLE

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == UserRole.FACILITATOR
        )


class IsEventOwner(BasePermission):
    message = ErrorCodes.FORBIDDEN_OWNERSHIP

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and obj.created_by_id == request.user.id

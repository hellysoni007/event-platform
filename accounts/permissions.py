from rest_framework.permissions import BasePermission

from accounts.models import UserRole


class IsSeeker(BasePermission):
    message = "Seeker role required."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == UserRole.SEEKER
        )


class IsFacilitator(BasePermission):
    message = "Facilitator role required."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == UserRole.FACILITATOR
        )

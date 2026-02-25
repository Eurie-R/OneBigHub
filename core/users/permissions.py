# users/permissions.py

from rest_framework.permissions import BasePermission


# ─────────────────────────────────────────────
# Permission: Organization Users Only
# REQ: SRS 4.1.2 Sub-Feature 6 - Access Control
# ─────────────────────────────────────────────

class IsOrganization(BasePermission):
    """
    Allows access only to users with the ORGANIZATION role.
    Used for: submitting proposals, reserving venues, posting to feed.
    """
    message = "Access denied. Only student organization accounts are allowed."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_org
        )


# ─────────────────────────────────────────────
# Permission: Administrative Office Users Only
# REQ: SRS 4.1.2 Sub-Feature 6 - Access Control
# ─────────────────────────────────────────────

class IsAdminOffice(BasePermission):
    """
    Allows access only to users with the ADMIN_OFFICE role.
    Used for: reviewing proposals, approving/rejecting reservations.
    """
    message = "Access denied. Only administrative office accounts are allowed."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_admin_office
        )


# ─────────────────────────────────────────────
# Permission: Either Role (any authenticated Ateneo user)
# REQ: SRS 4.1.2 Sub-Feature 6 - Access Control
# ─────────────────────────────────────────────

class IsAteneoUser(BasePermission):
    """
    Allows access to any authenticated user regardless of role.
    Used for: viewing the activity feed, viewing venue availability.
    """
    message = "Access denied. You must be logged in with an Ateneo account."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role is not None
        )


# ─────────────────────────────────────────────
# Permission: Profile Owner Only
# REQ: SRS 4.1.2 Sub-Feature 7 - Profile Viewing and Editing
# ─────────────────────────────────────────────

class IsProfileOwner(BasePermission):
    """
    Allows access only to the owner of a profile.
    Used for: editing org or admin office profile information.
    """
    message = "Access denied. You can only edit your own profile."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
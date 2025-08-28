# from rest_framework.permissions import BasePermission, SAFE_METHODS

# class IsEventManagerOrReadOnly(BasePermission):
   
#     # Custom permission:
#     #     - Faculty & Organization:
#     #     - Can create events.
#     #     - Can update/delete only their own events (handled in view).
#     # - Admin:
#     #     - Read-only access.
#     # - Others: No access.
   

#     def has_permission(self, request, view):
#         user = request.user
#         if user.is_department() or user.is_organization():
#             return True  # Allow, but object-level checked later
#         elif user.is_admin_user() and request.method in SAFE_METHODS:
#             return True  # Admin Read-only
#         return False  # Others denied

#     def has_object_permission(self, request, view, obj):
#         # Safe methods (GET, HEAD, OPTIONS) allowed for permitted users
#         if request.method in SAFE_METHODS:
#             return True
#         # Unsafe methods object-level check is handled in view for custom error message
#         return True  # Always allow, we handle stricter checks in view


from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsEventManagerOrReadOnly(BasePermission):
    # """
    # - Must be authenticated for everything.
    # - SAFE methods (GET/HEAD/OPTIONS): allowed to any authenticated user.
    # - UNSAFE methods (POST/PUT/PATCH/DELETE): only the event organizer may modify.
    #   (Creation policy can be enforced in the view if you want to limit who can POST.)
    # """

    def has_permission(self, request, view):
        user = request.user
        # Guard AnonymousUser
        if not user or not user.is_authenticated:
            return False

        # All authenticated users can READ
        if request.method in SAFE_METHODS:
            return True

        # For non-safe methods, defer to object-level (organizer check)
        return True

    def has_object_permission(self, request, view, obj):
        # Reads allowed to any authenticated user
        if request.method in SAFE_METHODS:
            return True

        # Writes only by organizer
        return obj.organizer_id == getattr(request.user, "id", None)
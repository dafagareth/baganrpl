# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwner(BasePermission):
    """Hanya user dengan role 'owner' yang boleh akses."""
    message = 'Hanya pemilik usaha yang dapat melakukan tindakan ini.'

    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.role == 'owner')

class IsOwnerOrReadOnly(BasePermission):
    """GET bebas (operator & owner), write hanya owner."""
    message = 'Hanya pemilik usaha yang dapat mengubah data master.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.role == 'owner')

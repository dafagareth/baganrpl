# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect


def is_owner(user):
    """True jika user punya profil dengan role 'owner'."""
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.role == 'owner')


class OwnerRequiredMixin(LoginRequiredMixin):
    """Batasi view hanya untuk owner.

    Operator yang login (mis. lewat web) diarahkan ke dashboard
    dengan pesan, bukan diberi error 403 mentah.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not is_owner(request.user):
            messages.warning(
                request,
                'Halaman ini khusus pemilik usaha.',
            )
            return redirect('operasional:trip_list')
        return super().dispatch(request, *args, **kwargs)

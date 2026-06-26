# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
#
# "Perekat" hak akses. Sistem punya dua peran: owner (pemilik) dan operator.
# Perannya disimpan di User.profile.role (lihat model UserProfile di apps/api).
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect


# Helper sederhana: cek apakah seorang user adalah owner.
def is_owner(user):
    """True jika user punya profil dengan role 'owner'."""
    # getattr(user, 'profile', None): ambil profile kalau ada, kalau tidak hasilnya None
    # (aman, tidak error walau user belum punya profil).
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.role == 'owner')


# Mixin = potongan kelas yang "ditempel" ke view lain lewat pewarisan untuk menambah perilaku.
# Mixin ini bikin sebuah view cuma bisa diakses owner. Dipakai di semua view data master.
class OwnerRequiredMixin(LoginRequiredMixin):
    """Batasi view hanya untuk owner.

    Operator yang login (mis. lewat web) diarahkan ke dashboard
    dengan pesan, bukan diberi error 403 mentah.
    """

    # dispatch() dijalankan pertama kali untuk setiap request ke view ini.
    def dispatch(self, request, *args, **kwargs):
        # sudah login tapi BUKAN owner -> tolak halus: kasih pesan lalu lempar ke daftar trip.
        if request.user.is_authenticated and not is_owner(request.user):
            messages.warning(
                request,
                'Halaman ini khusus pemilik usaha.',
            )
            return redirect('operasional:trip_list')
        # selebihnya lanjut seperti biasa (LoginRequiredMixin juga akan menendang yang belum login).
        return super().dispatch(request, *args, **kwargs)

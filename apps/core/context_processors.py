# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
#
# Context processor = fungsi yang nyuntik variabel ke SEMUA template otomatis,
# tanpa harus dikirim satu-satu dari tiap view. Didaftarkan di settings.py bagian
# TEMPLATES > context_processors. Berkat ini, {{ is_owner }} bisa dipakai di mana saja.
from .mixins import is_owner


def user_role(request):
    """Sediakan `is_owner` dan `trip_aktif` ke seluruh template."""
    ctx = {'is_owner': False, 'trip_aktif': None}
    if request.user.is_authenticated:
        ctx['is_owner'] = is_owner(request.user)
        # operator butuh tahu trip yang sedang jalan (buat shortcut di menu/dock).
        if not ctx['is_owner']:
            from apps.operasional.models import Trip
            # Kapal dipakai bersama, jadi trip aktif ditentukan per kapal bagan,
            # bukan per pembuat, supaya semua operator melihat trip yang sama.
            ctx['trip_aktif'] = Trip.objects.filter(
                kapal__jenis__icontains='bagan',
                status__in=['persiapan', 'berlayar'],
            ).select_related('kapal').first()
    return ctx

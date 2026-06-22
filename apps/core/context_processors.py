# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from .mixins import is_owner


def user_role(request):
    """Sediakan `is_owner` dan `trip_aktif` ke seluruh template."""
    ctx = {'is_owner': False, 'trip_aktif': None}
    if request.user.is_authenticated:
        ctx['is_owner'] = is_owner(request.user)
        if not ctx['is_owner']:
            from apps.operasional.models import Trip
            ctx['trip_aktif'] = Trip.objects.filter(
                dibuat_oleh=request.user,
                status__in=['persiapan', 'berlayar'],
            ).select_related('kapal').first()
    return ctx

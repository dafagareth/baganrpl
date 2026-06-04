# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from .mixins import is_owner


def user_role(request):
    """Sediakan `is_owner` ke seluruh template untuk kontrol menu."""
    return {'is_owner': is_owner(request.user) if request.user.is_authenticated else False}

# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
"""Paket views Operasional.

Dipecah per-domain agar tiap file < 300 baris, tapi tetap diakses sebagai
`views.NamaView` (urls.py memakai `from . import views`).
- feed.py  : feed gabungan aktivitas (dock Operasional)
- trip.py  : CRUD + transisi status Trip
- biaya.py : biaya operasional
- abk.py   : ABK pada trip
"""
from .feed import operasional_feed
from .trip import (
    TripListView,
    TripDetailView,
    TripCreateView,
    TripUpdateView,
    TripStatusUpdateView,
    TripDeleteView,
    TripBerlayarView,
    TripSelesaiView,
    TripQuickCreateView,
    TripLockView,
)
from .biaya import (
    BiayaCreateView,
    BiayaMultiCreateView,
    BiayaDeleteView,
)
from .abk import (
    TripAddABKView,
    TripRemoveABKView,
)

__all__ = [
    'operasional_feed',
    'TripListView',
    'TripDetailView',
    'TripCreateView',
    'TripUpdateView',
    'TripStatusUpdateView',
    'TripDeleteView',
    'TripBerlayarView',
    'TripSelesaiView',
    'TripQuickCreateView',
    'TripLockView',
    'BiayaCreateView',
    'BiayaMultiCreateView',
    'BiayaDeleteView',
    'TripAddABKView',
    'TripRemoveABKView',
]

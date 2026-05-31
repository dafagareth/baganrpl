# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
"""Views API dipecah per domain. Semua view di-re-export di sini agar
`from . import views` di urls.py tetap bekerja seperti sebelumnya."""

from .auth import (
    LoginView, MeView, MeFotoView, ChangePasswordView,
)
from .notifications import (
    RegisterDeviceView, NotificationListView, MarkNotificationsReadView,
)
from .master import (
    KapalListCreateView, KapalDetailView, KapalFotoView,
    ABKListCreateView, ABKDetailView,
    JenisIkanListCreateView, JenisIkanDetailView,
    PembeliListCreateView, PembeliDetailView,
)
from .records import (
    BiayaListView, HasilTangkapSemuaView, PenjualanListView,
    BiayaDetailView, HasilTangkapDetailView, PenjualanDetailView,
)
from .trips import (
    TripListView, TripCreateView, HasilTangkapTersediaView,
    TripDetailView, KunciLaporanView,
)
from .bagi_hasil import (
    BagiHasilListCreateView, BagiHasilDetailView,
)
from .reports import (
    DashboardView, LaporanChartsView, ArmadaChartsView, MapLokasiView,
)
from .accounts import (
    OperatorAccountListCreateView, OperatorAccountDetailView, ResetPasswordView,
    KapalOperatorView, ABKTersediaView,
)

__all__ = [
    'LoginView', 'MeView', 'MeFotoView', 'ChangePasswordView',
    'RegisterDeviceView', 'NotificationListView', 'MarkNotificationsReadView',
    'KapalListCreateView', 'KapalDetailView', 'KapalFotoView',
    'ABKListCreateView', 'ABKDetailView',
    'JenisIkanListCreateView', 'JenisIkanDetailView',
    'PembeliListCreateView', 'PembeliDetailView',
    'BiayaListView', 'HasilTangkapSemuaView', 'PenjualanListView',
    'BiayaDetailView', 'HasilTangkapDetailView', 'PenjualanDetailView',
    'TripListView', 'TripCreateView', 'HasilTangkapTersediaView',
    'TripDetailView', 'KunciLaporanView',
    'BagiHasilListCreateView', 'BagiHasilDetailView',
    'DashboardView', 'LaporanChartsView', 'ArmadaChartsView', 'MapLokasiView',
    'OperatorAccountListCreateView', 'OperatorAccountDetailView', 'ResetPasswordView',
    'KapalOperatorView', 'ABKTersediaView',
]

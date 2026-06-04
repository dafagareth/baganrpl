# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.utils import timezone
from django.views.generic import TemplateView
from apps.core.mixins import OwnerRequiredMixin
from .utils import get_rekap_periode, get_rekap_per_kapal


class LaporanIndexView(OwnerRequiredMixin, TemplateView):
    template_name = 'laporan/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        bulan = int(self.request.GET.get('bulan', now.month))
        tahun = int(self.request.GET.get('tahun', now.year))

        ctx['rekap']       = get_rekap_periode(bulan, tahun)
        ctx['rekap_kapal'] = get_rekap_per_kapal(tahun)
        ctx['bulan']       = bulan
        ctx['tahun']       = tahun
        ctx['bulan_list']  = range(1, 13)
        ctx['tahun_list']  = range(2023, now.year + 1)
        ctx['nama_bulan']  = [
            '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
        ]
        return ctx

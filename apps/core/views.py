# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
import json
from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import Count, F, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from apps.master.models import Kapal
from apps.operasional.models import BiayaOperasional, Trip
from apps.penjualan.models import Penjualan
from apps.tangkap.models import HasilTangkap

from .mixins import OwnerRequiredMixin

_NAMA_BULAN = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
               'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']


class PublicHomeView(TemplateView):
    template_name = 'master/public_home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        today = date.today()

        ctx['total_kapal']     = Kapal.objects.filter(status='aktif').count()
        ctx['trip_bulan_ini']  = Trip.objects.filter(
            tgl_berangkat__month=now.month, tgl_berangkat__year=now.year
        ).count()
        ctx['tangkap_bulan_ini'] = HasilTangkap.objects.filter(
            trip__tgl_berangkat__month=now.month,
            trip__tgl_berangkat__year=now.year,
        ).aggregate(total=Sum('berat_kg'))['total'] or 0

        ctx['lifetime_trip']       = Trip.objects.count()
        ctx['lifetime_tangkap']    = HasilTangkap.objects.aggregate(
            total=Sum('berat_kg'))['total'] or 0
        ctx['lifetime_pendapatan'] = Penjualan.objects.aggregate(
            total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0
        ctx['lifetime_biaya']      = BiayaOperasional.objects.aggregate(
            total=Sum('jumlah'))['total'] or 0

        trip_pertama = Trip.objects.order_by('tgl_berangkat').first()
        if trip_pertama:
            tb = trip_pertama.tgl_berangkat
            ctx['beroperasi_sejak'] = f"{_NAMA_BULAN[tb.month]} {tb.year}"
        else:
            ctx['beroperasi_sejak'] = '—'

        trip_selesai_n = Trip.objects.filter(status='selesai').count() or 1
        trip_total_n   = ctx['lifetime_trip'] or 1

        ctx['trip_selesai']            = trip_selesai_n
        ctx['pct_trip_sukses']         = round(trip_selesai_n / trip_total_n * 100)
        ctx['avg_pendapatan_per_trip'] = float(ctx['lifetime_pendapatan']) / trip_selesai_n
        ctx['avg_biaya_per_trip']      = float(ctx['lifetime_biaya']) / trip_selesai_n
        ctx['avg_laba_per_trip']       = (ctx['avg_pendapatan_per_trip']
                                          - ctx['avg_biaya_per_trip'])

        if ctx['avg_pendapatan_per_trip'] > 0:
            ctx['avg_margin_pct'] = round(
                ctx['avg_laba_per_trip'] / ctx['avg_pendapatan_per_trip'] * 100, 1)
        else:
            ctx['avg_margin_pct'] = 0

        if trip_pertama:
            bulan_aktif = max(1, (
                (now.year - trip_pertama.tgl_berangkat.year) * 12
                + (now.month - trip_pertama.tgl_berangkat.month) + 1
            ))
            ctx['avg_trip_per_bulan'] = round(ctx['lifetime_trip'] / bulan_aktif, 1)
            ctx['bulan_aktif'] = bulan_aktif
        else:
            ctx['avg_trip_per_bulan'] = 0
            ctx['bulan_aktif'] = 0

        ctx['kapal_aktif_list'] = Kapal.objects.filter(
            status='aktif').order_by('nama_kapal')
        ctx['top_ikan'] = list(
            HasilTangkap.objects.values('jenis_ikan__nama')
            .annotate(total_kg=Sum('berat_kg'))
            .order_by('-total_kg')[:5]
        )

        labels, pend_data, biaya_data, laba_data, tangkap_data = [], [], [], [], []
        for i in range(5, -1, -1):
            d = today - relativedelta(months=i)
            p = float(Penjualan.objects.filter(
                tgl_jual__month=d.month, tgl_jual__year=d.year
            ).aggregate(total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0)
            b = float(BiayaOperasional.objects.filter(
                trip__tgl_berangkat__month=d.month,
                trip__tgl_berangkat__year=d.year,
            ).aggregate(total=Sum('jumlah'))['total'] or 0)
            t = float(HasilTangkap.objects.filter(
                trip__tgl_berangkat__month=d.month,
                trip__tgl_berangkat__year=d.year,
            ).aggregate(total=Sum('berat_kg'))['total'] or 0)
            labels.append(f"{_NAMA_BULAN[d.month]}'{str(d.year)[2:]}")
            pend_data.append(p)
            biaya_data.append(b)
            laba_data.append(round(p - b, 2))
            tangkap_data.append(t)

        ctx['chart_labels']     = json.dumps(labels)
        ctx['chart_pendapatan'] = json.dumps(pend_data)
        ctx['chart_biaya']      = json.dumps(biaya_data)
        ctx['chart_laba']       = json.dumps(laba_data)
        ctx['chart_tangkap']    = json.dumps(tangkap_data)
        return ctx


class DashboardView(OwnerRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()

        ctx['total_kapal'] = Kapal.objects.filter(status='aktif').count()
        ctx['trip_bulan_ini'] = Trip.objects.filter(
            tgl_berangkat__month=today.month, tgl_berangkat__year=today.year
        ).count()
        ctx['tangkap_bulan_ini'] = HasilTangkap.objects.filter(
            trip__tgl_berangkat__month=today.month,
            trip__tgl_berangkat__year=today.year,
        ).aggregate(total=Sum('berat_kg'))['total'] or 0

        pendapatan_bulan = Penjualan.objects.filter(
            tgl_jual__month=today.month, tgl_jual__year=today.year
        ).aggregate(total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0
        biaya_bulan = BiayaOperasional.objects.filter(
            trip__tgl_berangkat__month=today.month,
            trip__tgl_berangkat__year=today.year,
        ).aggregate(total=Sum('jumlah'))['total'] or 0

        ctx['pendapatan_bulan_ini'] = pendapatan_bulan
        ctx['biaya_bulan_ini']      = biaya_bulan
        ctx['laba_bulan_ini']       = float(pendapatan_bulan) - float(biaya_bulan)
        ctx['trip_terbaru']         = Trip.objects.select_related('kapal').order_by('-tgl_berangkat')[:5]

        labels, pend_data, biaya_data, laba_data = [], [], [], []
        for i in range(5, -1, -1):
            d = today - relativedelta(months=i)
            p = float(Penjualan.objects.filter(
                tgl_jual__month=d.month, tgl_jual__year=d.year
            ).aggregate(total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0)
            b = float(BiayaOperasional.objects.filter(
                trip__tgl_berangkat__month=d.month,
                trip__tgl_berangkat__year=d.year,
            ).aggregate(total=Sum('jumlah'))['total'] or 0)
            labels.append(f"{_NAMA_BULAN[d.month]} '{str(d.year)[2:]}")
            pend_data.append(p)
            biaya_data.append(b)
            laba_data.append(round(p - b, 2))

        ctx['chart_labels']     = json.dumps(labels)
        ctx['chart_pendapatan'] = json.dumps(pend_data)
        ctx['chart_biaya']      = json.dumps(biaya_data)
        ctx['chart_laba']       = json.dumps(laba_data)

        top_ikan = list(HasilTangkap.objects.filter(
            trip__tgl_berangkat__month=today.month,
            trip__tgl_berangkat__year=today.year,
        ).values('jenis_ikan__nama').annotate(total=Sum('berat_kg')).order_by('-total')[:5])
        ctx['chart_ikan_labels'] = json.dumps([x['jenis_ikan__nama'] for x in top_ikan])
        ctx['chart_ikan_data']   = json.dumps([float(x['total']) for x in top_ikan])

        top_pembeli = list(Penjualan.objects.filter(
            tgl_jual__month=today.month, tgl_jual__year=today.year,
        ).values('pembeli__nama')
        .annotate(total=Sum(F('berat_terjual') * F('harga_per_kg')))
        .order_by('-total')[:5])
        ctx['chart_pembeli_labels'] = json.dumps([x['pembeli__nama'] for x in top_pembeli])
        ctx['chart_pembeli_data']   = json.dumps([float(x['total']) for x in top_pembeli])

        KAT = {'bbm': 'BBM', 'es': 'Es Balok', 'logistik': 'Logistik',
               'perawatan': 'Perawatan', 'lainnya': 'Lainnya'}
        kat_data = list(BiayaOperasional.objects.filter(
            trip__tgl_berangkat__year=today.year,
        ).values('kategori').annotate(total=Sum('jumlah')).order_by('-total'))
        ctx['chart_kat_labels'] = json.dumps([KAT.get(x['kategori'], x['kategori']) for x in kat_data])
        ctx['chart_kat_data']   = json.dumps([float(x['total']) for x in kat_data])

        util = list(Trip.objects.filter(tgl_berangkat__year=today.year)
                    .values('kapal__nama_kapal').annotate(jumlah=Count('id')).order_by('-jumlah'))
        ctx['chart_util_labels'] = json.dumps([x['kapal__nama_kapal'] for x in util])
        ctx['chart_util_data']   = json.dumps([x['jumlah'] for x in util])

        return ctx

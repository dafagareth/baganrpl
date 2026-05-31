# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from .models import Kapal, ABK, JenisIkan, Pembeli
from .forms import KapalForm, ABKForm, JenisIkanForm, PembeliForm

from django.views.generic import TemplateView
from django.utils import timezone
from apps.operasional.models import Trip
from apps.penjualan.models import Penjualan
from django.db.models import Sum, F

class KapalListView(LoginRequiredMixin, ListView):
    model = Kapal
    template_name = 'master/kapal_list.html'
    context_object_name = 'kapal_list'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nama_kapal__icontains=q) |
                Q(jenis__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx

class KapalCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Kapal
    form_class = KapalForm
    template_name = 'master/kapal_form.html'
    success_url = reverse_lazy('master:kapal_list')
    success_message = 'Data kapal berhasil ditambahkan'

class KapalUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Kapal
    form_class = KapalForm
    template_name = 'master/kapal_form.html'
    success_url = reverse_lazy('master:kapal_list')
    success_message = 'Data kapal berhasil diperbarui'

class KapalDeleteView(LoginRequiredMixin, DeleteView):
    model = Kapal
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('master:kapal_list')

class ABKListView(LoginRequiredMixin, ListView):
    model = ABK
    template_name = 'master/abk_list.html'
    context_object_name = 'abk_list'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nama__icontains=q) |
                Q(no_hp__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx

class ABKCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ABK
    form_class = ABKForm
    template_name = 'master/abk_form.html'
    success_url = reverse_lazy('master:abk_list')
    success_message = 'Data ABK berhasil ditambahkan'

class ABKUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ABK
    form_class = ABKForm
    template_name = 'master/abk_form.html'
    success_url = reverse_lazy('master:abk_list')
    success_message = 'Data ABK berhasil diperbarui'

class ABKDeleteView(LoginRequiredMixin, DeleteView):
    model = ABK
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('master:abk_list')

class JenisIkanListView(LoginRequiredMixin, ListView):
    model = JenisIkan
    template_name = 'master/ikan_list.html'
    context_object_name = 'ikan_list'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(nama__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx

class JenisIkanCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = JenisIkan
    form_class = JenisIkanForm
    template_name = 'master/ikan_form.html'
    success_url = reverse_lazy('master:ikan_list')
    success_message = 'Data jenis ikan berhasil ditambahkan'

class JenisIkanUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = JenisIkan
    form_class = JenisIkanForm
    template_name = 'master/ikan_form.html'
    success_url = reverse_lazy('master:ikan_list')
    success_message = 'Data jenis ikan berhasil diperbarui'

class JenisIkanDeleteView(LoginRequiredMixin, DeleteView):
    model = JenisIkan
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('master:ikan_list')

class PembeliListView(LoginRequiredMixin, ListView):
    model = Pembeli
    template_name = 'master/pembeli_list.html'
    context_object_name = 'pembeli_list'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nama__icontains=q) |
                Q(no_hp__icontains=q) |
                Q(alamat__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx

class PembeliCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Pembeli
    form_class = PembeliForm
    template_name = 'master/pembeli_form.html'
    success_url = reverse_lazy('master:pembeli_list')
    success_message = 'Data pembeli berhasil ditambahkan'

class PembeliUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Pembeli
    form_class = PembeliForm
    template_name = 'master/pembeli_form.html'
    success_url = reverse_lazy('master:pembeli_list')
    success_message = 'Data pembeli berhasil diperbarui'

class PembeliDeleteView(LoginRequiredMixin, DeleteView):
    model = Pembeli
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('master:pembeli_list')

class PublicHomeView(TemplateView):
    template_name = 'master/public_home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        import json
        from datetime import date
        from dateutil.relativedelta import relativedelta
        from apps.tangkap.models import HasilTangkap
        from apps.operasional.models import Trip, BiayaOperasional
        from apps.penjualan.models import Penjualan

        nama_bulan = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                      'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']

        ctx['total_kapal'] = Kapal.objects.filter(status='aktif').count()
        ctx['trip_bulan_ini'] = Trip.objects.filter(
            tgl_berangkat__month=now.month, tgl_berangkat__year=now.year
        ).count()
        ctx['tangkap_bulan_ini'] = HasilTangkap.objects.filter(
            trip__tgl_berangkat__month=now.month, trip__tgl_berangkat__year=now.year
        ).aggregate(total=Sum('berat_kg'))['total'] or 0

        ctx['lifetime_trip']      = Trip.objects.count()
        ctx['lifetime_tangkap']   = HasilTangkap.objects.aggregate(
            total=Sum('berat_kg'))['total'] or 0
        ctx['lifetime_pendapatan'] = Penjualan.objects.aggregate(
            total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0
        ctx['lifetime_biaya']     = BiayaOperasional.objects.aggregate(
            total=Sum('jumlah'))['total'] or 0

        # Bulan pertama trip tercatat (untuk "beroperasi sejak")
        trip_pertama = Trip.objects.order_by('tgl_berangkat').first()
        if trip_pertama:
            tb = trip_pertama.tgl_berangkat
            ctx['beroperasi_sejak'] = f"{nama_bulan[tb.month]} {tb.year}"
        else:
            ctx['beroperasi_sejak'] = '—'

        trip_selesai_qs = Trip.objects.filter(status='selesai')
        trip_selesai_n  = trip_selesai_qs.count() or 1
        trip_total_n    = ctx['lifetime_trip'] or 1

        ctx['trip_selesai']        = trip_selesai_qs.count()
        ctx['pct_trip_sukses']     = round(trip_selesai_qs.count() / trip_total_n * 100)
        ctx['avg_pendapatan_per_trip'] = float(ctx['lifetime_pendapatan']) / trip_selesai_n
        ctx['avg_biaya_per_trip']      = float(ctx['lifetime_biaya']) / trip_selesai_n
        ctx['avg_laba_per_trip']       = ctx['avg_pendapatan_per_trip'] - ctx['avg_biaya_per_trip']

        # Margin laba %
        if ctx['avg_pendapatan_per_trip'] > 0:
            ctx['avg_margin_pct'] = round(
                ctx['avg_laba_per_trip'] / ctx['avg_pendapatan_per_trip'] * 100, 1)
        else:
            ctx['avg_margin_pct'] = 0

        # Rata-rata trip per bulan (dari bulan pertama sampai sekarang)
        if trip_pertama:
            from dateutil.relativedelta import relativedelta as rd
            bulan_aktif = max(1, (
                (now.year - trip_pertama.tgl_berangkat.year) * 12 +
                (now.month - trip_pertama.tgl_berangkat.month) + 1
            ))
            ctx['avg_trip_per_bulan'] = round(ctx['lifetime_trip'] / bulan_aktif, 1)
            ctx['bulan_aktif'] = bulan_aktif
        else:
            ctx['avg_trip_per_bulan'] = 0
            ctx['bulan_aktif'] = 0

        ctx['kapal_aktif_list'] = Kapal.objects.filter(
            status='aktif').order_by('nama_kapal')

        from django.db.models import Sum as DSum
        top_ikan = HasilTangkap.objects.values(
            'jenis_ikan__nama'
        ).annotate(total_kg=DSum('berat_kg')).order_by('-total_kg')[:5]
        ctx['top_ikan'] = list(top_ikan)

        bulan_labels, pendapatan_data, biaya_data, laba_data, tangkap_data = [], [], [], [], []
        for i in range(5, -1, -1):
            d = date.today() - relativedelta(months=i)
            label = f"{nama_bulan[d.month]}'{str(d.year)[2:]}"
            bulan_labels.append(label)

            p = Penjualan.objects.filter(
                tgl_jual__month=d.month, tgl_jual__year=d.year
            ).aggregate(total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0
            b = BiayaOperasional.objects.filter(
                trip__tgl_berangkat__month=d.month, trip__tgl_berangkat__year=d.year
            ).aggregate(total=Sum('jumlah'))['total'] or 0
            t = HasilTangkap.objects.filter(
                trip__tgl_berangkat__month=d.month, trip__tgl_berangkat__year=d.year
            ).aggregate(total=Sum('berat_kg'))['total'] or 0

            pendapatan_data.append(float(p))
            biaya_data.append(float(b))
            laba_data.append(float(p) - float(b))
            tangkap_data.append(float(t))

        ctx['chart_labels']     = json.dumps(bulan_labels)
        ctx['chart_pendapatan'] = json.dumps(pendapatan_data)
        ctx['chart_biaya']      = json.dumps(biaya_data)
        ctx['chart_laba']       = json.dumps(laba_data)
        ctx['chart_tangkap']    = json.dumps(tangkap_data)
        return ctx

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        import json
        from datetime import date
        from dateutil.relativedelta import relativedelta

        from apps.tangkap.models import HasilTangkap

        ctx['total_kapal'] = Kapal.objects.filter(status='aktif').count()

        ctx['tangkap_bulan_ini'] = HasilTangkap.objects.filter(
            trip__tgl_berangkat__month=now.month,
            trip__tgl_berangkat__year=now.year
        ).aggregate(total=Sum('berat_kg'))['total'] or 0

        ctx['trip_bulan_ini'] = Trip.objects.filter(
            tgl_berangkat__month=now.month,
            tgl_berangkat__year=now.year
        ).count()
        ctx['pendapatan_bulan_ini'] = Penjualan.objects.filter(
            tgl_jual__month=now.month,
            tgl_jual__year=now.year
        ).aggregate(
            total=Sum(F('berat_terjual') * F('harga_per_kg'))
        )['total'] or 0
        ctx['trip_terbaru'] = Trip.objects.select_related('kapal').order_by('-tgl_berangkat')[:5]

        # Chart data: last 6 months revenue & costs
        bulan_labels = []
        pendapatan_data = []
        biaya_data = []
        nama_bulan = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                       'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']

        for i in range(5, -1, -1):
            try:
                d = date.today() - relativedelta(months=i)
            except Exception:
                # Fallback if python-dateutil not installed
                m = now.month - i
                y = now.year
                while m <= 0:
                    m += 12
                    y -= 1
                d = date(y, m, 1)

            bulan_labels.append(f"{nama_bulan[d.month]} {d.year}")

            pendapatan = Penjualan.objects.filter(
                tgl_jual__month=d.month,
                tgl_jual__year=d.year
            ).aggregate(
                total=Sum(F('berat_terjual') * F('harga_per_kg'))
            )['total'] or 0
            pendapatan_data.append(float(pendapatan))

            from apps.operasional.models import BiayaOperasional
            biaya = BiayaOperasional.objects.filter(
                trip__tgl_berangkat__month=d.month,
                trip__tgl_berangkat__year=d.year
            ).aggregate(total=Sum('jumlah'))['total'] or 0
            biaya_data.append(float(biaya))

        ctx['chart_labels'] = json.dumps(bulan_labels)
        ctx['chart_pendapatan'] = json.dumps(pendapatan_data)
        ctx['chart_biaya'] = json.dumps(biaya_data)

        return ctx
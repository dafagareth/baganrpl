# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views import View
from django.db.models import Q

from ..models import Trip, TripABK
from ..forms import TripForm, BiayaOperasionalForm, TripABKForm, TripStatusForm
from apps.tangkap.forms import HasilTangkapForm
from apps.core.mixins import is_owner


def _autolock_trip_lama(kapal):
    """Kunci laporan trip 'selesai' kapal ini yang owner lupa kunci, saat trip baru dibuat."""
    Trip.objects.filter(
        kapal=kapal, status='selesai', is_laporan_locked=False
    ).update(is_laporan_locked=True)


class TripListView(LoginRequiredMixin, ListView):
    model = Trip
    template_name = 'operasional/trip_list.html'
    context_object_name = 'trip_list'
    paginate_by = 15

    def get_queryset(self):
        # Kapal dipakai bersama — operator melihat semua trip, bukan hanya buatannya.
        qs = super().get_queryset().select_related('kapal')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(kapal__nama_kapal__icontains=q) |
                Q(status__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        from apps.master.models import Kapal
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['trip_form'] = TripForm()
        ctx['kapal_pilihan'] = Kapal.objects.filter(
            jenis__icontains='bagan', status='aktif'
        ).order_by('nama_kapal')
        return ctx


class TripDetailView(LoginRequiredMixin, DetailView):
    model = Trip
    template_name = 'operasional/trip_detail.html'
    context_object_name = 'trip'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['biaya_list'] = self.object.biaya_operasional.all()
        ctx['abk_list'] = self.object.trip_abk.select_related('abk').all()
        ctx['hasil_list'] = self.object.hasil_tangkap.select_related('jenis_ikan').all()
        # Forms for modals
        ctx['biaya_form'] = BiayaOperasionalForm()
        ctx['abk_form'] = TripABKForm(trip=self.object)
        ctx['tangkap_form'] = HasilTangkapForm()
        ctx['trip_edit_form'] = TripForm(instance=self.object)
        ctx['trip_status_form'] = TripStatusForm(instance=self.object)
        ctx['tangkap_edit_forms'] = [
            (h, HasilTangkapForm(instance=h))
            for h in ctx['hasil_list']
        ]
        ctx['bagi_hasil_list'] = self.object.bagi_hasil.select_related('abk').order_by('abk__nama')
        from apps.penjualan.models import Penjualan
        from apps.penjualan.forms import PenjualanForm
        ctx['penjualan_list'] = Penjualan.objects.filter(
            hasil_tangkap__trip=self.object
        ).select_related('pembeli', 'hasil_tangkap__jenis_ikan').order_by('-tgl_jual')
        ctx['penjualan_form'] = PenjualanForm(trip=self.object)
        return ctx


class TripCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'operasional/trip_form.html'
    success_message = 'Trip berhasil ditambahkan'

    def form_valid(self, form):
        form.instance.dibuat_oleh = self.request.user
        _autolock_trip_lama(form.cleaned_data['kapal'])
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to trip detail after creation so user can add ABK, biaya, etc.
        return reverse('operasional:trip_detail', kwargs={'pk': self.object.pk})


class TripUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'operasional/trip_form.html'
    success_message = 'Trip berhasil diperbarui'

    def dispatch(self, request, *args, **kwargs):
        trip = self.get_object()
        if trip.status == 'selesai' and not request.user.is_superuser:
            messages.error(request, 'Trip sudah selesai — hanya admin yang bisa mengedit.')
            return redirect('operasional:trip_detail', pk=trip.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('operasional:trip_detail', kwargs={'pk': self.object.pk})


class TripStatusUpdateView(LoginRequiredMixin, View):
    """Owner mengubah status trip saja (bukan kapal/tanggal)."""

    def post(self, request, pk):
        if not is_owner(request.user) and not request.user.is_superuser:
            messages.error(request, 'Hanya pemilik yang bisa mengubah status trip.')
            return redirect('operasional:trip_detail', pk=pk)
        trip = get_object_or_404(Trip, pk=pk)
        if trip.is_laporan_locked and not request.user.is_superuser:
            messages.error(request, 'Laporan dikunci — status tidak bisa diubah.')
            return redirect('operasional:trip_detail', pk=pk)
        form = TripStatusForm(request.POST, instance=trip)
        if form.is_valid():
            trip = form.save(commit=False)
            if trip.status == 'selesai' and not trip.tgl_kembali:
                trip.tgl_kembali = timezone.now().date()
            trip.save()
            messages.success(request, 'Status trip diperbarui.')
        else:
            messages.warning(request, 'Status tidak valid.')
        return redirect('operasional:trip_detail', pk=pk)


class TripDeleteView(LoginRequiredMixin, DeleteView):
    model = Trip
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('operasional:trip_list')


class TripBerlayarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk)
        if trip.status == 'persiapan':
            if not trip.trip_abk.exists():
                messages.warning(request, 'Pilih minimal satu ABK sebelum berlayar.')
                return redirect('operasional:trip_detail', pk=pk)
            trip.status = 'berlayar'
            trip.save(update_fields=['status'])
            messages.success(request, 'Kapal sudah berlayar.')
        return redirect('operasional:trip_detail', pk=pk)


class TripSelesaiView(LoginRequiredMixin, View):
    def post(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk)
        if trip.status == 'berlayar':
            trip.status = 'selesai'
            trip.tgl_kembali = timezone.now().date()
            trip.save(update_fields=['status', 'tgl_kembali'])
            messages.success(request, 'Trip selesai. Catat hasil tangkap sekarang.')
        return redirect('operasional:trip_detail', pk=pk)


class TripQuickCreateView(LoginRequiredMixin, View):
    """Buat trip seketika — kapal bagan pertama + tgl_berangkat hari ini."""

    def post(self, request):
        from apps.master.models import Kapal
        from datetime import date as _date
        kapal_qs = Kapal.objects.filter(jenis__icontains='bagan', status='aktif')
        kapal_id = request.POST.get('kapal')
        kapal = kapal_qs.filter(pk=kapal_id).first() if kapal_id else kapal_qs.first()
        if not kapal:
            messages.error(request, 'Tidak ada kapal bagan aktif.')
            return redirect('operasional:trip_list')
        if Trip.objects.filter(kapal=kapal, status__in=['persiapan', 'berlayar']).exists():
            messages.warning(request, f'{kapal.nama_kapal} masih punya trip aktif.')
            return redirect('operasional:trip_list')
        _autolock_trip_lama(kapal)
        trip = Trip.objects.create(
            kapal=kapal,
            tgl_berangkat=_date.today(),
            status='persiapan',
            dibuat_oleh=request.user,
        )
        messages.success(request, 'Trip baru dibuat.')
        return redirect('operasional:trip_detail', pk=trip.pk)


class TripLockView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from apps.core.mixins import is_owner as _is_owner
        trip = get_object_or_404(Trip, pk=pk)
        if not _is_owner(request.user) and not request.user.is_superuser:
            messages.error(request, 'Hanya pemilik yang bisa mengunci laporan.')
            return redirect('operasional:trip_detail', pk=pk)
        if trip.status == 'selesai' and not trip.is_laporan_locked:
            trip.is_laporan_locked = True
            trip.save(update_fields=['is_laporan_locked'])
            messages.success(request, 'Laporan berhasil dikunci. Data tidak bisa diubah lagi.')
        return redirect('operasional:trip_detail', pk=pk)

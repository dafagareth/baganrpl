# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from datetime import datetime, timezone as dt_timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views import View
from django.db.models import Q
from .models import Trip, TripABK, BiayaOperasional
from .forms import TripForm, BiayaOperasionalForm, BiayaOperasionalFormSet, TripABKForm, TripStatusForm
from apps.tangkap.forms import HasilTangkapForm
from apps.core.mixins import is_owner

_EPOCH = datetime(1970, 1, 1, tzinfo=dt_timezone.utc)


def _autolock_trip_lama(kapal):
    """Kunci laporan trip 'selesai' kapal ini yang owner lupa kunci, saat trip baru dibuat."""
    Trip.objects.filter(
        kapal=kapal, status='selesai', is_laporan_locked=False
    ).update(is_laporan_locked=True)


@login_required
def operasional_feed(request):
    """Tab Operasional (dock) — feed semua aktivitas (biaya/tangkap/jual) lintas trip."""
    from datetime import date as _date
    from apps.tangkap.models import HasilTangkap
    from apps.penjualan.models import Penjualan

    tipe = request.GET.get('tipe', 'semua')
    q = request.GET.get('q', '').strip()
    entries = []

    if tipe in ('semua', 'biaya'):
        bq = BiayaOperasional.objects.select_related('trip')
        if q:
            bq = bq.filter(Q(keterangan__icontains=q) | Q(kategori__icontains=q))
        for b in bq:
            tgl = b.dibuat_pada.date() if b.dibuat_pada else b.trip.tgl_berangkat
            entries.append({
                'tipe': 'biaya',
                'judul': b.keterangan or b.get_kategori_display(),
                'tgl': tgl,
                'nilai': b.jumlah,
                'satuan': 'rp',
            })

    if tipe in ('semua', 'tangkap'):
        tq = HasilTangkap.objects.select_related('trip', 'jenis_ikan')
        if q:
            tq = tq.filter(jenis_ikan__nama__icontains=q)
        for h in tq:
            tgl = h.dibuat_pada.date() if h.dibuat_pada else h.trip.tgl_berangkat
            entries.append({
                'tipe': 'tangkap',
                'judul': str(h.jenis_ikan),
                'tgl': tgl,
                'nilai': h.berat_kg,
                'satuan': 'kg',
            })

    if tipe in ('semua', 'jual'):
        jq = Penjualan.objects.select_related('hasil_tangkap__jenis_ikan')
        if q:
            jq = jq.filter(hasil_tangkap__jenis_ikan__nama__icontains=q)
        for p in jq:
            entries.append({
                'tipe': 'jual',
                'judul': str(p.hasil_tangkap.jenis_ikan),
                'tgl': p.tgl_jual,
                'nilai': p.total_nilai(),
                'satuan': 'jual',
            })

    entries.sort(key=lambda e: e['tgl'] or _date.min, reverse=True)

    trip_aktif = Trip.objects.filter(
        kapal__jenis__icontains='bagan',
        status__in=['persiapan', 'berlayar'],
    ).select_related('kapal').first()

    return render(request, 'operasional/feed.html', {
        'entries': entries,
        'tipe': tipe,
        'q': q,
        'trip_aktif': trip_aktif,
        'biaya_form': BiayaOperasionalForm(),
    })

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

class BiayaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = BiayaOperasional
    form_class = BiayaOperasionalForm
    template_name = 'operasional/biaya_form.html'
    success_message = 'Biaya berhasil ditambahkan'

    def dispatch(self, request, *args, **kwargs):
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        if trip.is_laporan_locked and not request.user.is_superuser:
            messages.error(request, 'Laporan dikunci — tidak bisa menambah biaya.')
            return redirect('operasional:trip_detail', pk=trip.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.trip_id = self.kwargs['trip_id']
        form.instance.kategori = 'lainnya'
        return super().form_valid(form)

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse('operasional:trip_detail', kwargs={'pk': self.kwargs['trip_id']})

class BiayaMultiCreateView(LoginRequiredMixin, View):
    """Tambah beberapa biaya (barang) sekaligus dalam satu form multi-baris."""
    template_name = 'operasional/biaya_multi.html'

    def dispatch(self, request, *args, **kwargs):
        self.trip = get_object_or_404(Trip, pk=kwargs['trip_id'])
        if self.trip.is_laporan_locked and not request.user.is_superuser:
            messages.error(request, 'Laporan dikunci — tidak bisa menambah biaya.')
            return redirect('operasional:trip_detail', pk=self.trip.pk)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, trip_id):
        formset = BiayaOperasionalFormSet(queryset=BiayaOperasional.objects.none())
        return render(request, self.template_name, {'formset': formset, 'trip': self.trip})

    def post(self, request, trip_id):
        formset = BiayaOperasionalFormSet(request.POST, queryset=BiayaOperasional.objects.none())
        if formset.is_valid():
            count = 0
            for form in formset:
                if form.cleaned_data.get('keterangan') and form.cleaned_data.get('jumlah') is not None:
                    biaya = form.save(commit=False)
                    biaya.trip = self.trip
                    biaya.kategori = 'lainnya'
                    biaya.save()
                    count += 1
            messages.success(request, f'{count} biaya ditambahkan.')
            return redirect('operasional:trip_detail', pk=self.trip.pk)
        return render(request, self.template_name, {'formset': formset, 'trip': self.trip})


class BiayaDeleteView(LoginRequiredMixin, View):
    """Delete a BiayaOperasional and redirect back to trip detail."""

    def post(self, request, pk):
        biaya = get_object_or_404(BiayaOperasional, pk=pk)
        trip_id = biaya.trip_id
        trip = biaya.trip
        if (trip.status == 'selesai' or trip.is_laporan_locked) and not request.user.is_superuser:
            messages.error(request, 'Trip sudah selesai atau laporan dikunci — tidak bisa menghapus biaya.')
            return redirect('operasional:trip_detail', pk=trip_id)
        biaya.delete()
        messages.success(request, 'Biaya berhasil dihapus')
        return redirect('operasional:trip_detail', pk=trip_id)

class TripAddABKView(LoginRequiredMixin, View):
    """Add multiple ABK to a trip via checkbox form."""

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        if (trip.status == 'selesai' or trip.is_laporan_locked) and not request.user.is_superuser:
            messages.error(request, 'Trip sudah selesai atau laporan dikunci — tidak bisa menambah ABK.')
            return redirect('operasional:trip_detail', pk=trip_id)
        form = TripABKForm(request.POST, trip=trip)
        if form.is_valid():
            abk_ids = form.cleaned_data['abk_ids']
            count = 0
            for abk_id in abk_ids:
                _, created = TripABK.objects.get_or_create(
                    trip=trip, abk_id=int(abk_id)
                )
                if created:
                    count += 1
            messages.success(request, f'{count} ABK berhasil ditambahkan')
        else:
            messages.warning(request, 'Pilih minimal satu ABK')
        return redirect('operasional:trip_detail', pk=trip_id)

class TripRemoveABKView(LoginRequiredMixin, View):
    """Remove a single ABK from a trip."""

    def post(self, request, trip_id, abk_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        if (trip.status == 'selesai' or trip.is_laporan_locked) and not request.user.is_superuser:
            messages.error(request, 'Trip sudah selesai atau laporan dikunci — tidak bisa menghapus ABK.')
            return redirect('operasional:trip_detail', pk=trip_id)
        trip_abk = get_object_or_404(TripABK, trip_id=trip_id, abk_id=abk_id)
        trip_abk.delete()
        messages.success(request, 'ABK berhasil dihapus dari trip')
        return redirect('operasional:trip_detail', pk=trip_id)


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
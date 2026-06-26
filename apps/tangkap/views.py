# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
#
# View untuk hasil tangkap. Operator hanya boleh menambah hasil tangkap kalau
# trip-nya sudah 'selesai' dan laporannya belum dikunci. Aturan itu dicek di
# method dispatch() sebelum form diproses.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q
from .models import HasilTangkap
from .forms import HasilTangkapForm


class HasilTangkapListView(LoginRequiredMixin, ListView):
    model = HasilTangkap
    template_name = 'tangkap/list.html'
    context_object_name = 'hasil_list'
    paginate_by = 15

    def get_queryset(self):
        # select_related ikut mengambil data trip, kapal, & jenis ikan dalam satu query
        # supaya tidak nembak database berkali-kali saat ditampilkan di tabel (hindari N+1).
        qs = HasilTangkap.objects.select_related(
            'trip__kapal', 'jenis_ikan'
        ).order_by('-trip__tgl_berangkat')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(jenis_ikan__nama__icontains=q) |
                Q(trip__kapal__nama_kapal__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        # Siapkan satu form edit untuk tiap baris (dipakai modal "ubah" di tabel).
        ctx['edit_forms'] = [
            (h, HasilTangkapForm(instance=h)) for h in ctx['hasil_list']
        ]
        return ctx


class HasilTangkapCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = HasilTangkap
    form_class = HasilTangkapForm
    template_name = 'tangkap/form.html'
    success_message = 'Hasil tangkap berhasil ditambahkan'

    # dispatch() jalan paling awal, sebelum get/post. Tempat pas untuk "satpam":
    # tolak akses kalau syaratnya tidak terpenuhi, lalu redirect balik.
    def dispatch(self, request, *args, **kwargs):
        from apps.operasional.models import Trip
        # get_object_or_404: ambil trip sesuai id, otomatis tampilkan 404 kalau tidak ada.
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        if trip.status != 'selesai':
            messages.error(request, 'Hasil tangkap hanya bisa diinput jika trip sudah selesai.')
            return redirect('operasional:trip_detail', pk=trip.pk)
        if trip.is_laporan_locked and not request.user.is_superuser:
            messages.error(request, 'Laporan sudah dikunci, tidak bisa menambah data.')
            return redirect('operasional:trip_detail', pk=trip.pk)
        return super().dispatch(request, *args, **kwargs)

    # form_valid jalan saat data form lolos validasi. Di sini kita tempelkan trip_id
    # (diambil dari URL) ke objek sebelum disimpan, karena tidak ada di form.
    def form_valid(self, form):
        form.instance.trip_id = self.kwargs['trip_id']
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.operasional.models import Trip
        ctx['trip'] = Trip.objects.get(pk=self.kwargs['trip_id'])
        return ctx

    # Setelah simpan, balik ke halaman detail trip yang bersangkutan.
    def get_success_url(self):
        return reverse('operasional:trip_detail', kwargs={'pk': self.kwargs['trip_id']})


class HasilTangkapUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = HasilTangkap
    form_class = HasilTangkapForm
    template_name = 'tangkap/form.html'
    success_message = 'Hasil tangkap berhasil diperbarui'

    def get_success_url(self):
        # self.object = objek yang barusan diedit; trip_id-nya dipakai untuk balik ke detail trip.
        return reverse('operasional:trip_detail', kwargs={'pk': self.object.trip_id})


class HasilTangkapDeleteView(LoginRequiredMixin, DeleteView):
    model = HasilTangkap
    template_name = 'master/confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.trip.is_laporan_locked and not request.user.is_superuser:
            messages.error(request, 'Laporan sudah dikunci, tidak bisa menghapus data.')
            return redirect('operasional:trip_detail', pk=obj.trip_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('operasional:trip_detail', kwargs={'pk': self.object.trip_id})

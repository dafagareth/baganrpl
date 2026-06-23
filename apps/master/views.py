# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import OwnerRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Count, Q
from .models import Kapal, ABK, JenisIkan, Pembeli
from .forms import KapalForm, ABKForm, JenisIkanForm, PembeliForm


class DataMasterIndexView(OwnerRequiredMixin, TemplateView):
    """Halaman hub Data Master — pintu masuk ke kapal, ABK, jenis ikan, pembeli."""
    template_name = 'master/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['kapal_count'] = Kapal.objects.count()
        ctx['abk_count'] = ABK.objects.count()
        ctx['ikan_count'] = JenisIkan.objects.count()
        ctx['pembeli_count'] = Pembeli.objects.count()
        return ctx

class KapalListView(OwnerRequiredMixin, ListView):
    model = Kapal
    template_name = 'master/kapal_list.html'
    context_object_name = 'kapal_list'
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().annotate(jml_trip=Count('trips')).order_by('nama_kapal')
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

class KapalCreateView(OwnerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Kapal
    form_class = KapalForm
    template_name = 'master/kapal_form.html'
    success_url = reverse_lazy('master:kapal_list')
    success_message = 'Data kapal berhasil ditambahkan'

class KapalUpdateView(OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Kapal
    form_class = KapalForm
    template_name = 'master/kapal_form.html'
    success_url = reverse_lazy('master:kapal_list')
    success_message = 'Data kapal berhasil diperbarui'

class KapalDeleteView(OwnerRequiredMixin, DeleteView):
    model = Kapal
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('master:kapal_list')

    def post(self, request, *args, **kwargs):
        # Kapal yang punya riwayat trip tidak dihapus permanen (jaga data laporan) —
        # cukup dinonaktifkan agar tidak muncul lagi di pilihan trip baru.
        kapal = self.get_object()
        if kapal.trips.exists():
            if kapal.status != 'nonaktif':
                kapal.status = 'nonaktif'
                kapal.save(update_fields=['status'])
            messages.info(
                request,
                f'Kapal {kapal.nama_kapal} punya riwayat trip, jadi dinonaktifkan '
                '(bukan dihapus) supaya data laporan tetap utuh.'
            )
            return redirect('master:kapal_list')
        messages.success(request, f'Kapal {kapal.nama_kapal} berhasil dihapus.')
        return super().post(request, *args, **kwargs)

class ABKListView(OwnerRequiredMixin, ListView):
    model = ABK
    template_name = 'master/abk_list.html'
    context_object_name = 'abk_list'
    paginate_by = 15

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

class ABKCreateView(OwnerRequiredMixin, SuccessMessageMixin, CreateView):
    model = ABK
    form_class = ABKForm
    template_name = 'master/abk_form.html'
    success_url = reverse_lazy('master:abk_list')
    success_message = 'Data ABK berhasil ditambahkan'

class ABKUpdateView(OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ABK
    form_class = ABKForm
    template_name = 'master/abk_form.html'
    success_url = reverse_lazy('master:abk_list')
    success_message = 'Data ABK berhasil diperbarui'

class ABKDeleteView(OwnerRequiredMixin, DeleteView):
    model = ABK
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('master:abk_list')

class JenisIkanListView(OwnerRequiredMixin, ListView):
    model = JenisIkan
    template_name = 'master/ikan_list.html'
    context_object_name = 'ikan_list'
    paginate_by = 15

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

class JenisIkanCreateView(OwnerRequiredMixin, SuccessMessageMixin, CreateView):
    model = JenisIkan
    form_class = JenisIkanForm
    template_name = 'master/ikan_form.html'
    success_url = reverse_lazy('master:ikan_list')
    success_message = 'Data jenis ikan berhasil ditambahkan'

class JenisIkanUpdateView(OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = JenisIkan
    form_class = JenisIkanForm
    template_name = 'master/ikan_form.html'
    success_url = reverse_lazy('master:ikan_list')
    success_message = 'Data jenis ikan berhasil diperbarui'

class JenisIkanDeleteView(OwnerRequiredMixin, DeleteView):
    model = JenisIkan
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('master:ikan_list')

class PembeliListView(OwnerRequiredMixin, ListView):
    model = Pembeli
    template_name = 'master/pembeli_list.html'
    context_object_name = 'pembeli_list'
    paginate_by = 15

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

class PembeliCreateView(OwnerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Pembeli
    form_class = PembeliForm
    template_name = 'master/pembeli_form.html'
    success_url = reverse_lazy('master:pembeli_list')
    success_message = 'Data pembeli berhasil ditambahkan'

class PembeliUpdateView(OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Pembeli
    form_class = PembeliForm
    template_name = 'master/pembeli_form.html'
    success_url = reverse_lazy('master:pembeli_list')
    success_message = 'Data pembeli berhasil diperbarui'

class PembeliDeleteView(OwnerRequiredMixin, DeleteView):
    model = Pembeli
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('master:pembeli_list')


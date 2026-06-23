# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Sum, F, Q
from apps.core.mixins import OwnerRequiredMixin, is_owner
from .models import Penjualan, BagiHasil
from .forms import (
    PenjualanForm, PenjualanFormSet, BagiHasilForm, BagiHasilGlobalForm,
    BagiHasilMultiFormSet,
)

class PenjualanListView(LoginRequiredMixin, ListView):
    model = Penjualan
    template_name = 'penjualan/list.html'
    context_object_name = 'penjualan_list'
    paginate_by = 15

    def get_queryset(self):
        qs = Penjualan.objects.select_related(
            'hasil_tangkap__trip__kapal',
            'hasil_tangkap__jenis_ikan',
            'pembeli'
        ).order_by('-tgl_jual')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(hasil_tangkap__jenis_ikan__nama__icontains=q) |
                Q(hasil_tangkap__trip__kapal__nama_kapal__icontains=q) |
                Q(pembeli__nama__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_pendapatan'] = Penjualan.objects.aggregate(
            total=Sum(F('berat_terjual') * F('harga_per_kg'))
        )['total'] or 0
        ctx['q'] = self.request.GET.get('q', '')
        return ctx

class PenjualanCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Penjualan
    form_class = PenjualanForm
    template_name = 'penjualan/form.html'
    success_url = reverse_lazy('penjualan:list')
    success_message = 'Data penjualan berhasil ditambahkan'

class PenjualanCreateForTripView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Tambah penjualan dari dalam trip — tangkapan difilter ke trip tsb."""
    model = Penjualan
    form_class = PenjualanForm
    template_name = 'penjualan/form.html'
    success_message = 'Penjualan berhasil ditambahkan'

    def dispatch(self, request, *args, **kwargs):
        from apps.operasional.models import Trip
        self.trip = get_object_or_404(Trip, pk=kwargs['trip_id'])
        if self.trip.is_laporan_locked and not request.user.is_superuser:
            messages.error(request, 'Laporan dikunci — tidak bisa menambah penjualan.')
            return redirect('operasional:trip_detail', pk=self.trip.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['trip'] = self.trip
        return kw

    def get_success_url(self):
        return reverse('operasional:trip_detail', kwargs={'pk': self.trip.pk})


class PenjualanUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Penjualan
    form_class = PenjualanForm
    template_name = 'penjualan/form.html'
    success_url = reverse_lazy('penjualan:list')
    success_message = 'Data penjualan berhasil diperbarui'

class PenjualanDeleteView(LoginRequiredMixin, DeleteView):
    model = Penjualan
    template_name = 'master/confirm_delete.html'
    success_url = reverse_lazy('penjualan:list')

@login_required
def penjualan_multi_create(request):
    """View untuk input banyak penjualan sekaligus."""
    if request.method == 'POST':
        formset = PenjualanFormSet(request.POST, queryset=Penjualan.objects.none())
        if formset.is_valid():
            instances = formset.save()
            messages.success(request, f'{len(instances)} data penjualan berhasil ditambahkan')
            return redirect('penjualan:list')
    else:
        formset = PenjualanFormSet(queryset=Penjualan.objects.none())
    # Get stock data from first form in formset
    stock_data_json = '{}'
    if formset.forms:
        form = formset.forms[0]
        if hasattr(form, 'stock_data_json'):
            stock_data_json = form.stock_data_json
    return render(request, 'penjualan/form_multi.html', {
        'formset': formset,
        'stock_data_json': stock_data_json,
    })

@login_required
def bagi_hasil_mark_paid(request, pk):
    bh = get_object_or_404(BagiHasil, pk=pk)
    if not is_owner(request.user):
        raise PermissionDenied
    if request.method == 'POST' and not bh.sudah_dibayar:
        bh.sudah_dibayar = True
        bh.tgl_bayar = date.today()
        bh.save(update_fields=['sudah_dibayar', 'tgl_bayar'])
        messages.success(request, f'Bagi hasil {bh.abk.nama} ditandai lunas.')
    next_url = request.POST.get('next') or reverse('penjualan:bagi_hasil_list')
    return redirect(next_url)


class BagiHasilListView(OwnerRequiredMixin, ListView):
    model = BagiHasil
    template_name = 'penjualan/bagi_hasil_list.html'
    context_object_name = 'bagi_hasil_list'

    def get_queryset(self):
        return BagiHasil.objects.select_related(
            'trip__kapal', 'abk'
        ).order_by('-trip__tgl_berangkat')

class BagiHasilCreateView(OwnerRequiredMixin, SuccessMessageMixin, CreateView):
    model = BagiHasil
    form_class = BagiHasilForm
    template_name = 'penjualan/bagi_hasil_form.html'
    success_message = 'Bagi hasil berhasil ditambahkan'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        from apps.operasional.models import Trip
        trip = get_object_or_404(Trip, id=self.kwargs['trip_id'])
        kwargs['trip'] = trip
        return kwargs

    def form_valid(self, form):
        from apps.operasional.models import Trip
        trip = Trip.objects.get(id=self.kwargs['trip_id'])
        form.instance.trip = trip
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('operasional:trip_detail', kwargs={'pk': self.kwargs['trip_id']})

class BagiHasilMultiCreateView(OwnerRequiredMixin, View):
    """Tambah bagi hasil beberapa ABK sekaligus (multi-baris) untuk satu trip."""
    template_name = 'penjualan/bagi_hasil_multi.html'

    def dispatch(self, request, *args, **kwargs):
        from apps.operasional.models import Trip
        self.trip = get_object_or_404(Trip, pk=kwargs['trip_id'])
        if self.trip.is_laporan_locked and not request.user.is_superuser:
            messages.error(request, 'Laporan dikunci — tidak bisa menambah bagi hasil.')
            return redirect('operasional:trip_detail', pk=self.trip.pk)
        return super().dispatch(request, *args, **kwargs)

    def _abk_queryset(self):
        from apps.operasional.models import TripABK
        from apps.master.models import ABK
        existing = BagiHasil.objects.filter(trip=self.trip).values_list('abk_id', flat=True)
        trip_abk = TripABK.objects.filter(trip=self.trip).values_list('abk_id', flat=True)
        return ABK.objects.filter(id__in=trip_abk).exclude(id__in=existing)

    def _bind_abk(self, formset):
        qs = self._abk_queryset()
        for form in formset:
            form.fields['abk'].queryset = qs
        return formset

    def get(self, request, trip_id):
        formset = self._bind_abk(BagiHasilMultiFormSet(queryset=BagiHasil.objects.none()))
        return render(request, self.template_name, {'formset': formset, 'trip': self.trip})

    def post(self, request, trip_id):
        formset = self._bind_abk(BagiHasilMultiFormSet(request.POST, queryset=BagiHasil.objects.none()))
        if formset.is_valid():
            count = 0
            seen = set()
            for form in formset:
                abk = form.cleaned_data.get('abk')
                nominal = form.cleaned_data.get('nominal')
                if abk and nominal is not None and abk.id not in seen:
                    BagiHasil.objects.create(trip=self.trip, abk=abk, nominal=nominal)
                    seen.add(abk.id)
                    count += 1
            messages.success(request, f'{count} bagi hasil ditambahkan.')
            return redirect('operasional:trip_detail', pk=self.trip.pk)
        return render(request, self.template_name, {'formset': formset, 'trip': self.trip})


class BagiHasilCreateGlobalView(OwnerRequiredMixin, SuccessMessageMixin, CreateView):
    model = BagiHasil
    form_class = BagiHasilGlobalForm
    template_name = 'penjualan/bagi_hasil_form.html'
    success_message = 'Bagi hasil berhasil ditambahkan'
    success_url = reverse_lazy('penjualan:bagi_hasil_list')

class BagiHasilUpdateView(OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = BagiHasil
    form_class = BagiHasilForm
    template_name = 'penjualan/bagi_hasil_form.html'
    success_message = 'Bagi hasil berhasil diperbarui'
    success_url = reverse_lazy('penjualan:bagi_hasil_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.get_object().trip
        return kwargs
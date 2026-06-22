# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import OwnerRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Sum, F, Q
from .models import Penjualan, BagiHasil
from .forms import PenjualanForm, PenjualanFormSet, BagiHasilForm, BagiHasilGlobalForm

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
        ctx['edit_forms'] = [
            (p, PenjualanForm(instance=p)) for p in ctx['penjualan_list']
        ]
        return ctx

class PenjualanCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Penjualan
    form_class = PenjualanForm
    template_name = 'penjualan/form.html'
    success_url = reverse_lazy('penjualan:list')
    success_message = 'Data penjualan berhasil ditambahkan'

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
# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse
from django.views.generic import CreateView
from django.views import View

from ..models import Trip, BiayaOperasional
from ..forms import BiayaOperasionalForm, BiayaOperasionalFormSet


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

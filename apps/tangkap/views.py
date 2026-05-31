# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.shortcuts import render

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from .models import HasilTangkap
from .forms import HasilTangkapForm

class HasilTangkapListView(LoginRequiredMixin, ListView):
    model = HasilTangkap
    template_name = 'tangkap/list.html'
    context_object_name = 'hasil_list'

    def get_queryset(self):
        return HasilTangkap.objects.select_related(
            'trip__kapal', 'jenis_ikan'
        ).order_by('-trip__tgl_berangkat')

class HasilTangkapCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = HasilTangkap
    form_class = HasilTangkapForm
    template_name = 'tangkap/form.html'
    success_message = 'Hasil tangkap berhasil ditambahkan'

    def dispatch(self, request, *args, **kwargs):
        from apps.operasional.models import Trip
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        if trip.status != 'selesai':
            messages.error(request, 'Hasil tangkap hanya bisa diinput jika trip sudah selesai.')
            return redirect('operasional:trip_detail', pk=trip.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.trip_id = self.kwargs['trip_id']
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.operasional.models import Trip
        ctx['trip'] = Trip.objects.get(pk=self.kwargs['trip_id'])
        return ctx

    def get_success_url(self):
        return reverse('operasional:trip_detail', kwargs={'pk': self.kwargs['trip_id']})

class HasilTangkapUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = HasilTangkap
    form_class = HasilTangkapForm
    template_name = 'tangkap/form.html'
    success_message = 'Hasil tangkap berhasil diperbarui'

    def get_success_url(self):
        return reverse('operasional:trip_detail', kwargs={'pk': self.object.trip_id})

class HasilTangkapDeleteView(LoginRequiredMixin, DeleteView):
    model = HasilTangkap
    template_name = 'master/confirm_delete.html'

    def get_success_url(self):
        return reverse('operasional:trip_detail', kwargs={'pk': self.object.trip_id})
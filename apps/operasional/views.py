# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views import View
from django.db.models import Q
from .models import Trip, TripABK, BiayaOperasional
from .forms import TripForm, BiayaOperasionalForm, TripABKForm
from apps.tangkap.forms import HasilTangkapForm

class TripListView(LoginRequiredMixin, ListView):
    model = Trip
    template_name = 'operasional/trip_list.html'
    context_object_name = 'trip_list'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset().select_related('kapal')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(kapal__nama_kapal__icontains=q) |
                Q(status__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
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
        return ctx

class TripCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'operasional/trip_form.html'
    success_message = 'Trip berhasil ditambahkan'

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
        if trip.status == 'selesai' and not request.user.is_superuser:
            messages.error(request, 'Trip sudah selesai — tidak bisa menambah biaya.')
            return redirect('operasional:trip_detail', pk=trip.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.trip_id = self.kwargs['trip_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('operasional:trip_detail', kwargs={'pk': self.kwargs['trip_id']})

class BiayaDeleteView(LoginRequiredMixin, View):
    """Delete a BiayaOperasional and redirect back to trip detail."""

    def post(self, request, pk):
        biaya = get_object_or_404(BiayaOperasional, pk=pk)
        trip_id = biaya.trip_id
        trip = biaya.trip
        if trip.status == 'selesai' and not request.user.is_superuser:
            messages.error(request, 'Trip sudah selesai — tidak bisa menghapus biaya.')
            return redirect('operasional:trip_detail', pk=trip_id)
        biaya.delete()
        messages.success(request, 'Biaya berhasil dihapus')
        return redirect('operasional:trip_detail', pk=trip_id)

class TripAddABKView(LoginRequiredMixin, View):
    """Add multiple ABK to a trip via checkbox form."""

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        if trip.status == 'selesai' and not request.user.is_superuser:
            messages.error(request, 'Trip sudah selesai — tidak bisa menambah ABK.')
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
        if trip.status == 'selesai' and not request.user.is_superuser:
            messages.error(request, 'Trip sudah selesai — tidak bisa menghapus ABK.')
            return redirect('operasional:trip_detail', pk=trip_id)
        trip_abk = get_object_or_404(TripABK, trip_id=trip_id, abk_id=abk_id)
        trip_abk.delete()
        messages.success(request, 'ABK berhasil dihapus dari trip')
        return redirect('operasional:trip_detail', pk=trip_id)
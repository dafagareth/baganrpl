# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View

from ..models import Trip, TripABK
from ..forms import TripABKForm


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

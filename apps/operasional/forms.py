# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django import forms
from .models import Trip, TripABK, BiayaOperasional
from apps.master.models import ABK

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['kapal', 'tgl_berangkat', 'tgl_kembali', 'status', 'catatan']
        widgets = {
            'kapal': forms.Select(attrs={'class': 'form-select'}),
            'tgl_berangkat': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tgl_kembali': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        kapal = cleaned_data.get('kapal')
        status = cleaned_data.get('status')

        if kapal and status == 'berlayar':
            # Cari trip lain dari kapal yang sama yang sedang berlayar
            qs = Trip.objects.filter(kapal=kapal, status='berlayar')
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    f"Kapal {kapal.nama_kapal} sedang dalam pelayaran (status: Sedang Berlayar). "
                    "Satu kapal tidak boleh memiliki lebih dari satu trip aktif secara bersamaan."
                )
        return cleaned_data

class BiayaOperasionalForm(forms.ModelForm):
    class Meta:
        model = BiayaOperasional
        fields = ['kategori', 'jumlah', 'keterangan']
        widgets = {
            'kategori': forms.Select(attrs={'class': 'form-select'}),
            'jumlah': forms.NumberInput(attrs={'class': 'form-control'}),
            'keterangan': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TripABKForm(forms.Form):
    """Multi-select checkbox form for adding ABK to a trip."""
    abk_ids = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label='Pilih ABK'
    )

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only active ABK that are NOT already in this trip
        existing_ids = []
        if trip:
            existing_ids = TripABK.objects.filter(trip=trip).values_list('abk_id', flat=True)
        available_abk = ABK.objects.filter(aktif=True).exclude(id__in=existing_ids)
        self.fields['abk_ids'].choices = [
            (abk.id, abk.nama)
            for abk in available_abk
        ]
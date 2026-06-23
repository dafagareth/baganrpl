# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django import forms
from .models import Trip, TripABK, BiayaOperasional
from apps.master.models import ABK

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['kapal', 'tgl_berangkat']
        widgets = {
            'kapal'        : forms.Select(attrs={'class': 'form-select'}),
            'tgl_berangkat': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.master.models import Kapal
        from datetime import date
        kapal_qs = Kapal.objects.filter(jenis__icontains='bagan', status='aktif')
        self.fields['kapal'].queryset = kapal_qs
        if not self.instance.pk:
            self.fields['tgl_berangkat'].initial = date.today()
        if kapal_qs.count() == 1:
            if not self.instance.pk:
                self.fields['kapal'].initial = kapal_qs.first()
            self.fields['kapal'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        kapal = cleaned_data.get('kapal')
        if kapal:
            qs = Trip.objects.filter(kapal=kapal, status__in=['persiapan', 'berlayar'])
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Kapal {kapal.nama_kapal} masih memiliki trip aktif. "
                    "Selesaikan trip sebelumnya terlebih dahulu."
                )
        return cleaned_data

class TripStatusForm(forms.ModelForm):
    """Owner hanya boleh mengubah status trip (bukan kapal/tanggal)."""
    class Meta:
        model = Trip
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class BiayaOperasionalForm(forms.ModelForm):
    """Input biaya operator — cukup nama barang + jumlah (tanpa kategori)."""
    class Meta:
        model = BiayaOperasional
        fields = ['keterangan', 'jumlah']
        labels = {'keterangan': 'Barang', 'jumlah': 'Jumlah (Rp)'}
        widgets = {
            'keterangan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama barang / pengeluaran'}),
            'jumlah': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['keterangan'].required = True


BiayaOperasionalFormSet = forms.modelformset_factory(
    BiayaOperasional, form=BiayaOperasionalForm, extra=1, can_delete=False,
)

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
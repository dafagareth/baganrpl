# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django import forms
from .models import Trip, TripABK, BiayaOperasional
from apps.master.models import ABK


# Form buat/edit Trip. Hanya minta kapal + tanggal berangkat; sisanya diisi sistem.
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
        # pilihan kapal dibatasi: jenis mengandung 'bagan' dan statusnya aktif
        kapal_qs = Kapal.objects.filter(jenis__icontains='bagan', status='aktif')
        self.fields['kapal'].queryset = kapal_qs
        # self.instance.pk kosong artinya ini data BARU (bukan edit) -> isi tanggal default hari ini
        if not self.instance.pk:
            self.fields['tgl_berangkat'].initial = date.today()
        # kalau cuma ada satu kapal, gak perlu disuruh memilih: pilihkan otomatis & sembunyikan
        if kapal_qs.count() == 1:
            if not self.instance.pk:
                self.fields['kapal'].initial = kapal_qs.first()
            self.fields['kapal'].widget = forms.HiddenInput()

    # Cegah satu kapal punya dua trip aktif sekaligus (harus selesaikan yang lama dulu).
    def clean(self):
        cleaned_data = super().clean()
        kapal = cleaned_data.get('kapal')
        if kapal:
            qs = Trip.objects.filter(kapal=kapal, status__in=['persiapan', 'berlayar'])
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)   # jangan hitung trip ini sendiri saat edit
            if qs.exists():
                raise forms.ValidationError(
                    f"Kapal {kapal.nama_kapal} masih memiliki trip aktif. "
                    "Selesaikan trip sebelumnya terlebih dahulu."
                )
        return cleaned_data


# Form khusus owner untuk ganti status trip saja (kapal & tanggal tidak bisa diubah di sini).
class TripStatusForm(forms.ModelForm):
    """Owner hanya boleh mengubah status trip (bukan kapal/tanggal)."""
    class Meta:
        model = Trip
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


# Form biaya versi operator: cukup nama barang + jumlah, kategori diisi otomatis di view.
class BiayaOperasionalForm(forms.ModelForm):
    """Input biaya operator: cukup nama barang + jumlah (tanpa kategori)."""
    class Meta:
        model = BiayaOperasional
        fields = ['keterangan', 'jumlah']
        labels = {'keterangan': 'Barang', 'jumlah': 'Jumlah (Rp)'}   # ganti teks label di form
        widgets = {
            'keterangan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama barang / pengeluaran'}),
            'jumlah': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['keterangan'].required = True   # nama barang wajib diisi (di model boleh kosong)


# Formset = beberapa BiayaOperasionalForm sekaligus untuk input banyak biaya dalam satu halaman.
BiayaOperasionalFormSet = forms.modelformset_factory(
    BiayaOperasional, form=BiayaOperasionalForm, extra=1, can_delete=False,
)


# Bukan ModelForm: form biasa berisi daftar checkbox untuk memilih beberapa ABK sekaligus.
class TripABKForm(forms.Form):
    """Form centang banyak ABK untuk dimasukkan ke trip."""
    abk_ids = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label='Pilih ABK'
    )

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Pilihan = ABK aktif yang BELUM ada di trip ini (yang sudah masuk tidak ditawarkan lagi).
        existing_ids = []
        if trip:
            existing_ids = TripABK.objects.filter(trip=trip).values_list('abk_id', flat=True)
        available_abk = ABK.objects.filter(aktif=True).exclude(id__in=existing_ids)
        # choices diisi manual: daftar pasangan (nilai, label) -> (id ABK, nama ABK).
        self.fields['abk_ids'].choices = [
            (abk.id, abk.nama)
            for abk in available_abk
        ]

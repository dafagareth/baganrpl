# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django import forms
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from django.db.models.functions import Coalesce
import json
from .models import Penjualan, BagiHasil
from apps.operasional.models import Trip
from apps.tangkap.models import HasilTangkap
from apps.master.models import ABK

# File ini berisi semua form penjualan & bagi hasil. Bagian yang perlu diperhatikan:
# - PenjualanForm: cuma boleh jual ikan yang stoknya masih ada, dan tidak melebihi stok.
# - BagiHasilForm: cuma boleh kasih jatah ke ABK yang ikut trip, dan tidak dobel.
# Aturan-aturan itu ada di method __init__ (membatasi pilihan) dan clean (validasi akhir).


# Form jual untuk SATU transaksi (dipakai modal "Tambah jual" di detail trip).
class PenjualanForm(forms.ModelForm):
    class Meta:
        model = Penjualan
        fields = ['hasil_tangkap', 'pembeli', 'berat_terjual', 'harga_per_kg', 'tgl_jual', 'catatan']
        widgets = {
            'hasil_tangkap': forms.Select(attrs={'class': 'form-select'}),
            'pembeli': forms.Select(attrs={'class': 'form-select'}),
            'berat_terjual': forms.NumberInput(attrs={'class': 'form-control'}),
            'harga_per_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'tgl_jual': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    # __init__ dipanggil saat form dibuat. trip= dikirim dari view supaya pilihan ikan
    # dibatasi ke trip itu saja. Kita juga hitung sisa stok tiap ikan biar yang habis tidak muncul.
    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Hitung di database: total terjual per ikan, lalu tersedia = berat tangkap - terjual.
        # Coalesce(..., 0.0): kalau belum ada penjualan (NULL), anggap 0.
        # ExpressionWrapper: bungkus operasi pengurangan antar-kolom + tetapkan tipenya Decimal.
        qs = HasilTangkap.objects.annotate(
            terjual=Coalesce(Sum('penjualan__berat_terjual'), 0.0, output_field=DecimalField())
        ).annotate(
            tersedia=ExpressionWrapper(F('berat_kg') - F('terjual'), output_field=DecimalField())
        )
        if trip is not None:
            qs = qs.filter(trip=trip)
        if self.instance and self.instance.pk:
            # Saat EDIT: tampilkan yang stoknya > 0, plus ikan yang sedang dipakai baris ini
            # (walaupun stoknya 0) supaya pilihan lamanya tetap kelihatan.
            qs = qs.filter(Q(tersedia__gt=0) | Q(pk=self.instance.hasil_tangkap.pk))
        else:
            qs = qs.filter(tersedia__gt=0)   # saat TAMBAH: hanya yang masih ada stok
        self.fields['hasil_tangkap'].queryset = qs
        # Data stok per-ikan untuk tombol "Semua" di JS (isi otomatis berat = sisa stok).
        self._stock_data = {ht.pk: float(ht.tersedia) for ht in qs}

    # @property: dipanggil tanpa kurung (form.stock_data_json). Ubah dict stok jadi teks JSON
    # supaya bisa ditaruh di atribut HTML dan dibaca JavaScript.
    @property
    def stock_data_json(self):
        return json.dumps(self._stock_data)

    # clean(): validasi terakhir yang melibatkan beberapa field sekaligus. Di sini cek
    # supaya berat yang dijual tidak melebihi stok yang tersedia.
    def clean(self):
        cleaned_data = super().clean()
        hasil_tangkap = cleaned_data.get('hasil_tangkap')
        berat_terjual = cleaned_data.get('berat_terjual')
        if hasil_tangkap and berat_terjual is not None:
            tersedia = hasil_tangkap.berat_tersedia
            # Kalau ini proses EDIT pada ikan yang sama, kembalikan dulu berat lamanya
            # ke "tersedia" supaya tidak terhitung dobel (kalau tidak, edit jadi salah dianggap kelebihan).
            if self.instance and self.instance.pk and self.instance.hasil_tangkap_id == hasil_tangkap.pk:
                tersedia += self.instance.berat_terjual
            if berat_terjual > tersedia:
                # raise ValidationError = batalkan simpan, tampilkan pesan error ke user.
                raise forms.ValidationError(
                    f'Stok tidak cukup! Tersedia {tersedia:g} kg, '
                    f'tapi diinput {berat_terjual:g} kg.'
                )
        return cleaned_data

# Versi ringkas PenjualanForm untuk input BANYAK baris sekaligus (tabel multi-input).
# Logikanya mirip (batasi ke ikan yang masih ada stok + cek tidak melebihi stok),
# bedanya widget-nya kecil (kelas form-*-sm) biar muat dalam tabel.
class PenjualanMultiForm(forms.ModelForm):
    """Form ringkas untuk input penjualan multi-baris."""
    class Meta:
        model = Penjualan
        fields = ['hasil_tangkap', 'pembeli', 'berat_terjual', 'harga_per_kg', 'tgl_jual', 'catatan']
        widgets = {
            'hasil_tangkap': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'pembeli': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'berat_terjual': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'harga_per_kg': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '1'}),
            'tgl_jual': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'catatan': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Opsional'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = HasilTangkap.objects.annotate(
            terjual=Coalesce(Sum('penjualan__berat_terjual'), 0.0, output_field=DecimalField())
        ).annotate(
            tersedia=ExpressionWrapper(F('berat_kg') - F('terjual'), output_field=DecimalField())
        ).filter(tersedia__gt=0)
        self.fields['hasil_tangkap'].queryset = qs
        self._stock_data = {ht.pk: float(ht.tersedia) for ht in qs}

    @property
    def stock_data_json(self):
        return json.dumps(self._stock_data)

    def clean(self):
        cleaned_data = super().clean()
        hasil_tangkap = cleaned_data.get('hasil_tangkap')
        berat_terjual = cleaned_data.get('berat_terjual')
        if hasil_tangkap and berat_terjual is not None:
            tersedia = hasil_tangkap.berat_tersedia
            if berat_terjual > tersedia:
                raise forms.ValidationError(
                    f'Stok tidak cukup! Tersedia {tersedia:g} kg, '
                    f'tapi diinput {berat_terjual:g} kg.'
                )
        return cleaned_data

# modelformset_factory: pabrik yang membuat "kumpulan form" dari satu form, supaya bisa
# input beberapa baris Penjualan dalam satu halaman. extra=1 = sediakan 1 baris kosong.
PenjualanFormSet = forms.modelformset_factory(
    Penjualan,
    form=PenjualanMultiForm,
    extra=1,
    can_delete=False,
)


# Form jatah bagi hasil per ABK. Nominal diisi manual oleh owner.
class BagiHasilForm(forms.ModelForm):
    class Meta:
        model = BagiHasil
        fields = ['abk', 'nominal', 'sudah_dibayar', 'tgl_bayar']
        widgets = {
            'abk': forms.Select(attrs={'class': 'form-select'}),
            'nominal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan nominal bagi hasil'}),
            'sudah_dibayar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tgl_bayar': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    # Batasi pilihan ABK: hanya yang ikut trip ini DAN belum punya jatah bagi hasil.
    def __init__(self, *args, trip=None, **kwargs):
        self.trip = trip
        super().__init__(*args, **kwargs)
        if trip:
            from apps.operasional.models import TripABK
            # ABK yang sudah punya bagi hasil di trip ini (biar tidak muncul lagi / tidak dobel).
            # values_list('abk_id', flat=True) = ambil daftar id-nya saja, bukan objek penuh.
            existing_abk_ids = BagiHasil.objects.filter(trip=trip).values_list('abk_id', flat=True)
            if self.instance and self.instance.pk:
                # Kalau lagi EDIT, jangan keluarkan ABK milik baris yang sedang diedit.
                existing_abk_ids = existing_abk_ids.exclude(abk_id=self.instance.abk.id)

            trip_abk_ids = TripABK.objects.filter(trip=trip).values_list('abk_id', flat=True)
            # Pilihan akhir = (ABK yang ikut trip) dikurangi (yang sudah dapat jatah).
            self.fields['abk'].queryset = ABK.objects.filter(
                id__in=trip_abk_ids
            ).exclude(
                id__in=existing_abk_ids
            )

    def clean(self):
        cleaned_data = super().clean()
        abk = cleaned_data.get('abk')
        trip = cleaned_data.get('trip') or getattr(self, 'trip', None)

        if not trip and self.instance and self.instance.pk:
            trip = self.instance.trip

        if trip and abk:
            from apps.operasional.models import TripABK
            # 1. Validasi: ABK harus terdaftar di trip tersebut
            if not TripABK.objects.filter(trip=trip, abk=abk).exists():
                raise forms.ValidationError(
                    f"ABK {abk.nama} tidak terdaftar dalam pelayaran (trip) {trip}."
                )

            # 2. Validasi: Satu ABK hanya bisa menerima satu bagi hasil per trip (tidak ganda)
            qs = BagiHasil.objects.filter(trip=trip, abk=abk)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Bagi hasil untuk ABK {abk.nama} pada trip ini sudah pernah diinput."
                )

        return cleaned_data

class BagiHasilGlobalForm(BagiHasilForm):
    class Meta(BagiHasilForm.Meta):
        fields = ['trip', 'abk', 'nominal', 'sudah_dibayar', 'tgl_bayar']
        widgets = BagiHasilForm.Meta.widgets.copy()
        widgets['trip'] = forms.Select(attrs={'class': 'form-select'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tampilkan Trip terbaru terlebih dahulu
        self.fields['trip'].queryset = Trip.objects.order_by('-tgl_berangkat')


class BagiHasilMultiForm(forms.ModelForm):
    """Satu baris bagi hasil: pilih ABK + nominal (untuk input multi-baris)."""
    class Meta:
        model = BagiHasil
        fields = ['abk', 'nominal']
        widgets = {
            'abk': forms.Select(attrs={'class': 'form-select'}),
            'nominal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nominal (Rp)'}),
        }


BagiHasilMultiFormSet = forms.modelformset_factory(
    BagiHasil, form=BagiHasilMultiForm, extra=1, can_delete=False,
)
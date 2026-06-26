# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django import forms
from .models import HasilTangkap


# ModelForm = form yang field-nya otomatis dibuat dari model. Kita cukup sebut
# model & daftar field-nya, Django yang urus tipe input + validasinya.
class HasilTangkapForm(forms.ModelForm):
    class Meta:
        model = HasilTangkap
        # field yang boleh diisi user. lat/lng ikut tapi disembunyikan (diisi GPS, bukan diketik).
        fields = ['jenis_ikan', 'berat_kg', 'kondisi', 'catatan', 'foto_bukti', 'lat', 'lng']
        # widgets = atur tampilan tiap input. 'class': 'form-...' itu kelas Bootstrap biar rapi.
        widgets = {
            'jenis_ikan': forms.Select(attrs={'class': 'form-select'}),
            'berat_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'kondisi': forms.Select(attrs={'class': 'form-select'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'lat': forms.HiddenInput(),   # tidak tampil di layar
            'lng': forms.HiddenInput(),
        }

# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django import forms
from .models import HasilTangkap

class HasilTangkapForm(forms.ModelForm):
    class Meta:
        model = HasilTangkap
        fields = ['jenis_ikan', 'berat_kg', 'kondisi', 'catatan', 'foto_bukti', 'lat', 'lng']
        widgets = {
            'jenis_ikan': forms.Select(attrs={'class': 'form-select'}),
            'berat_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'kondisi': forms.Select(attrs={'class': 'form-select'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'lat': forms.HiddenInput(),
            'lng': forms.HiddenInput(),
        }
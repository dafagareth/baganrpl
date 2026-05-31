# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django import forms
from .models import Kapal, ABK, JenisIkan, Pembeli

class KapalForm(forms.ModelForm):
    class Meta:
        model = Kapal
        fields = '__all__'
        widgets = {
            'nama_kapal': forms.TextInput(attrs={'class': 'form-control'}),
            'jenis': forms.TextInput(attrs={'class': 'form-control'}),
            'kapasitas': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ABKForm(forms.ModelForm):
    class Meta:
        model = ABK
        fields = '__all__'
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'no_hp': forms.TextInput(attrs={'class': 'form-control'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class JenisIkanForm(forms.ModelForm):
    class Meta:
        model = JenisIkan
        fields = '__all__'
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'satuan': forms.TextInput(attrs={'class': 'form-control'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PembeliForm(forms.ModelForm):
    class Meta:
        model = Pembeli
        fields = '__all__'
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'no_hp': forms.TextInput(attrs={'class': 'form-control'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
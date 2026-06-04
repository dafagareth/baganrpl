# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from rest_framework import serializers

from apps.master.models import Kapal, ABK, JenisIkan, Pembeli


class KapalSerializer(serializers.ModelSerializer):
    foto_url      = serializers.SerializerMethodField()
    operator_list = serializers.SerializerMethodField()
    has_operator  = serializers.SerializerMethodField()

    class Meta:
        model = Kapal
        fields = ['id', 'nama_kapal', 'jenis', 'kapasitas', 'status',
                  'keterangan', 'foto_url', 'operator_list', 'has_operator']

    def get_foto_url(self, obj):
        if not obj.foto:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.foto.url) if request else obj.foto.url

    def get_operator_list(self, obj):
        return [
            {'id': a.operator_id, 'username': a.operator.username,
             'nama': a.operator.get_full_name() or ''}
            for a in obj.operator_assignments.select_related('operator').all()
        ]

    def get_has_operator(self, obj):
        return obj.operator_assignments.exists()


class ABKSerializer(serializers.ModelSerializer):
    class Meta:
        model = ABK
        fields = ['id', 'nama', 'no_hp', 'alamat', 'aktif']


class JenisIkanSerializer(serializers.ModelSerializer):
    class Meta:
        model = JenisIkan
        fields = ['id', 'nama', 'satuan', 'keterangan', 'harga_minimum']


class PembeliSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pembeli
        fields = ['id', 'nama', 'no_hp', 'alamat', 'keterangan']

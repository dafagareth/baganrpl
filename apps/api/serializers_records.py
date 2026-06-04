# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from rest_framework import serializers

from apps.operasional.models import BiayaOperasional
from apps.tangkap.models import HasilTangkap
from apps.penjualan.models import Penjualan


class BiayaRiwayatSerializer(serializers.ModelSerializer):
    kapal_nama     = serializers.CharField(source='trip.kapal.nama_kapal', read_only=True)
    tgl_berangkat  = serializers.DateField(source='trip.tgl_berangkat',    read_only=True)
    trip_id        = serializers.IntegerField(source='trip.id',            read_only=True)
    kategori_label = serializers.CharField(source='get_kategori_display',  read_only=True)
    trip_status    = serializers.CharField(source='trip.status',           read_only=True)
    foto_bukti_url = serializers.SerializerMethodField()

    class Meta:
        model = BiayaOperasional
        fields = ['id', 'trip_id', 'kapal_nama', 'tgl_berangkat',
                  'kategori', 'kategori_label', 'jumlah', 'keterangan',
                  'foto_bukti_url', 'trip_status', 'dibuat_pada']

    def get_foto_bukti_url(self, obj):
        if not obj.foto_bukti:
            return None
        request = self.context.get('request')
        url = obj.foto_bukti.url
        return request.build_absolute_uri(url) if request else url


class HasilTangkapRiwayatSerializer(serializers.ModelSerializer):
    kapal_nama     = serializers.CharField(source='trip.kapal.nama_kapal', read_only=True)
    tgl_berangkat  = serializers.DateField(source='trip.tgl_berangkat',    read_only=True)
    trip_id        = serializers.IntegerField(source='trip.id',            read_only=True)
    jenis_ikan_nama = serializers.CharField(source='jenis_ikan.nama',      read_only=True)
    kondisi_label   = serializers.CharField(source='get_kondisi_display',  read_only=True)
    foto_bukti_url  = serializers.SerializerMethodField()
    trip_is_laporan_locked = serializers.BooleanField(
        source='trip.is_laporan_locked', read_only=True)

    class Meta:
        model = HasilTangkap
        fields = ['id', 'trip_id', 'kapal_nama', 'tgl_berangkat',
                  'jenis_ikan', 'jenis_ikan_nama', 'berat_kg',
                  'kondisi', 'kondisi_label', 'catatan', 'foto_bukti_url',
                  'trip_is_laporan_locked', 'dibuat_pada']

    def get_foto_bukti_url(self, obj):
        if not obj.foto_bukti:
            return None
        request = self.context.get('request')
        url = obj.foto_bukti.url
        return request.build_absolute_uri(url) if request else url


class PenjualanRiwayatSerializer(serializers.ModelSerializer):
    kapal_nama    = serializers.CharField(
        source='hasil_tangkap.trip.kapal.nama_kapal', read_only=True)
    trip_id       = serializers.IntegerField(
        source='hasil_tangkap.trip.id', read_only=True)
    jenis_ikan_nama = serializers.CharField(
        source='hasil_tangkap.jenis_ikan.nama', read_only=True)
    pembeli_nama   = serializers.CharField(source='pembeli.nama',          read_only=True)
    total          = serializers.SerializerMethodField()
    foto_bukti_url = serializers.SerializerMethodField()
    trip_is_laporan_locked = serializers.BooleanField(
        source='hasil_tangkap.trip.is_laporan_locked', read_only=True)

    class Meta:
        model = Penjualan
        fields = ['id', 'trip_id', 'kapal_nama', 'jenis_ikan_nama', 'pembeli_nama',
                  'berat_terjual', 'harga_per_kg', 'total', 'tgl_jual', 'catatan',
                  'foto_bukti_url', 'trip_is_laporan_locked', 'dibuat_pada']

    def get_total(self, obj):
        return float(obj.berat_terjual * obj.harga_per_kg)

    def get_foto_bukti_url(self, obj):
        if not obj.foto_bukti:
            return None
        request = self.context.get('request')
        url = obj.foto_bukti.url
        return request.build_absolute_uri(url) if request else url

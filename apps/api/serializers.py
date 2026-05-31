# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.master.models import Kapal, ABK, JenisIkan, Pembeli, OperatorKapal
from apps.operasional.models import Trip, TripABK, BiayaOperasional
from apps.tangkap.models import HasilTangkap
from apps.penjualan.models import BagiHasil, Penjualan

from .models import DeviceToken, Notification

class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login JWT yang sekaligus mengembalikan role & username."""

    def validate(self, attrs):
        data = super().validate(attrs)
        profile = getattr(self.user, 'profile', None)
        data['role'] = profile.role if profile else None
        data['username'] = self.user.username
        return data

class MeSerializer(serializers.Serializer):
    username  = serializers.CharField()
    nama      = serializers.CharField(allow_blank=True)
    role      = serializers.CharField()
    is_staff  = serializers.BooleanField()
    foto_url  = serializers.CharField(allow_null=True)

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['token', 'platform']
        # Hapus UniqueValidator bawaan DRF — view pakai update_or_create,
        # token yang sama boleh di-update ke user lain (ganti HP / re-login).
        extra_kwargs = {'token': {'validators': []}}

class NotificationSerializer(serializers.ModelSerializer):
    pengirim_nama    = serializers.SerializerMethodField()
    pengirim_foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'event', 'judul', 'pesan', 'dibaca', 'dibuat',
                  'pengirim_nama', 'pengirim_foto_url']

    def get_pengirim_nama(self, obj):
        if not obj.pengirim:
            return None
        return obj.pengirim.get_full_name() or obj.pengirim.username

    def get_pengirim_foto_url(self, obj):
        if not obj.pengirim:
            return None
        profile = getattr(obj.pengirim, 'profile', None)
        if not profile or not profile.foto:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(profile.foto.url) if request else profile.foto.url

class KapalSerializer(serializers.ModelSerializer):
    foto_url     = serializers.SerializerMethodField()
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

class TripSerializer(serializers.ModelSerializer):
    kapal_nama     = serializers.CharField(source='kapal.nama_kapal', read_only=True)
    kapal_foto_url = serializers.SerializerMethodField()
    total_pendapatan = serializers.SerializerMethodField()
    total_biaya    = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ['id', 'kapal', 'kapal_nama', 'kapal_foto_url',
                  'tgl_berangkat', 'tgl_kembali', 'status', 'is_laporan_locked',
                  'total_pendapatan', 'total_biaya']

    def get_kapal_foto_url(self, obj):
        if not obj.kapal.foto:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.kapal.foto.url) if request else obj.kapal.foto.url

    def get_total_pendapatan(self, obj):
        return float(obj.total_pendapatan())

    def get_total_biaya(self, obj):
        return float(obj.total_biaya_operasional())

class HasilTangkapSerializer(serializers.ModelSerializer):
    jenis_ikan_nama = serializers.CharField(source='jenis_ikan.nama', read_only=True)
    kapal_nama = serializers.CharField(source='trip.kapal.nama_kapal', read_only=True)
    berat_tersedia = serializers.ReadOnlyField()

    class Meta:
        model = HasilTangkap
        fields = ['id', 'trip', 'kapal_nama', 'jenis_ikan', 'jenis_ikan_nama',
                  'berat_kg', 'berat_tersedia', 'kondisi']

class BagiHasilSerializer(serializers.ModelSerializer):
    abk_nama = serializers.CharField(source='abk.nama', read_only=True)

    class Meta:
        model = BagiHasil
        fields = ['id', 'trip', 'abk', 'abk_nama', 'nominal',
                  'sudah_dibayar', 'tgl_bayar']
        read_only_fields = ['id']

    def validate(self, attrs):
        # Pastikan ABK ini terdaftar di trip (via TripABK)
        trip = attrs.get('trip') or (self.instance.trip if self.instance else None)
        abk = attrs.get('abk') or (self.instance.abk if self.instance else None)
        if trip and abk:
            from apps.operasional.models import TripABK
            if not TripABK.objects.filter(trip=trip, abk=abk).exists():
                raise serializers.ValidationError(
                    {'abk': f'ABK "{abk.nama}" tidak terdaftar di trip ini.'})
        return attrs

class TripDetailSerializer(serializers.ModelSerializer):
    """Detail trip lengkap: keuangan + biaya + tangkap + penjualan + ABK."""
    kapal_nama = serializers.CharField(source='kapal.nama_kapal', read_only=True)
    total_pendapatan = serializers.SerializerMethodField()
    total_biaya = serializers.SerializerMethodField()
    laba_kotor = serializers.SerializerMethodField()
    total_bagi_hasil = serializers.SerializerMethodField()
    laba_bersih = serializers.SerializerMethodField()
    abk_list = serializers.SerializerMethodField()
    biaya_list = serializers.SerializerMethodField()
    hasil_tangkap_list = serializers.SerializerMethodField()
    penjualan_list = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ['id', 'kapal', 'kapal_nama', 'tgl_berangkat', 'tgl_kembali',
                  'status', 'is_laporan_locked', 'catatan',
                  'total_pendapatan', 'total_biaya', 'laba_kotor',
                  'total_bagi_hasil', 'laba_bersih',
                  'abk_list', 'biaya_list', 'hasil_tangkap_list', 'penjualan_list']

    def get_total_pendapatan(self, obj):
        return float(obj.total_pendapatan())

    def get_total_biaya(self, obj):
        return float(obj.total_biaya_operasional())

    def get_laba_kotor(self, obj):
        return float(obj.laba_kotor())

    def get_total_bagi_hasil(self, obj):
        return float(obj.total_bagi_hasil())

    def get_laba_bersih(self, obj):
        return float(obj.laba_bersih())

    def get_abk_list(self, obj):
        result = []
        for ta in obj.trip_abk.select_related('abk').all():
            bh = BagiHasil.objects.filter(trip=obj, abk=ta.abk).first()
            result.append({
                'abk_id': ta.abk.id,
                'abk_nama': ta.abk.nama,
                'bagi_hasil_id': bh.id if bh else None,
                'nominal': float(bh.nominal) if bh else None,
                'sudah_dibayar': bh.sudah_dibayar if bh else False,
                'tgl_bayar': str(bh.tgl_bayar) if bh and bh.tgl_bayar else None,
            })
        return result

    def get_biaya_list(self, obj):
        request = self.context.get('request')
        result = []
        for b in obj.biaya_operasional.all():
            foto_url = None
            if b.foto_bukti:
                raw = b.foto_bukti.url
                foto_url = request.build_absolute_uri(raw) if request else raw
            result.append({
                'id': b.id,
                'kategori': b.get_kategori_display(),
                'jumlah': float(b.jumlah),
                'keterangan': b.keterangan or '',
                'foto_bukti_url': foto_url,
            })
        return result

    def get_hasil_tangkap_list(self, obj):
        request = self.context.get('request')
        result = []
        for h in obj.hasil_tangkap.select_related('jenis_ikan').all():
            foto_url = None
            if h.foto_bukti:
                raw = h.foto_bukti.url
                foto_url = request.build_absolute_uri(raw) if request else raw
            result.append({
                'id': h.id,
                'jenis_ikan': h.jenis_ikan.nama,
                'berat_kg': float(h.berat_kg),
                'berat_tersedia': float(h.berat_tersedia),
                'kondisi': h.get_kondisi_display(),
                'catatan': h.catatan or '',
                'foto_bukti_url': foto_url,
            })
        return result

    def get_penjualan_list(self, obj):
        penjualan = Penjualan.objects.filter(
            hasil_tangkap__trip=obj
        ).select_related('pembeli', 'hasil_tangkap__jenis_ikan')
        request = self.context.get('request')
        result = []
        for p in penjualan:
            foto_url = None
            if p.foto_bukti:
                raw = p.foto_bukti.url
                foto_url = request.build_absolute_uri(raw) if request else raw
            result.append({
                'id': p.id,
                'jenis_ikan': p.hasil_tangkap.jenis_ikan.nama,
                'pembeli': p.pembeli.nama,
                'berat_terjual': float(p.berat_terjual),
                'harga_per_kg': float(p.harga_per_kg),
                'total': float(p.berat_terjual * p.harga_per_kg),
                'tgl_jual': str(p.tgl_jual),
                'foto_bukti_url': foto_url,
            })
        return result

class TripCreateSerializer(serializers.ModelSerializer):
    abk_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, default=[]
    )

    class Meta:
        model = Trip
        fields = ['id', 'kapal', 'tgl_berangkat', 'tgl_kembali',
                  'status', 'catatan', 'abk_ids', 'lat', 'lng']
        read_only_fields = ['id']

    def create(self, validated_data):
        abk_ids = validated_data.pop('abk_ids', [])
        trip = Trip.objects.create(**validated_data)
        for abk_id in abk_ids:
            TripABK.objects.get_or_create(trip=trip, abk_id=abk_id)
        return trip

class BiayaRiwayatSerializer(serializers.ModelSerializer):
    kapal_nama    = serializers.CharField(source='trip.kapal.nama_kapal', read_only=True)
    tgl_berangkat = serializers.DateField(source='trip.tgl_berangkat',    read_only=True)
    trip_id       = serializers.IntegerField(source='trip.id',            read_only=True)
    kategori_label = serializers.CharField(source='get_kategori_display', read_only=True)
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
    kapal_nama    = serializers.CharField(source='trip.kapal.nama_kapal', read_only=True)
    tgl_berangkat = serializers.DateField(source='trip.tgl_berangkat',    read_only=True)
    trip_id       = serializers.IntegerField(source='trip.id',            read_only=True)
    jenis_ikan_nama = serializers.CharField(source='jenis_ikan.nama',     read_only=True)
    kondisi_label   = serializers.CharField(source='get_kondisi_display', read_only=True)
    foto_bukti_url  = serializers.SerializerMethodField()
    trip_is_laporan_locked = serializers.BooleanField(source='trip.is_laporan_locked', read_only=True)

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
    pembeli_nama  = serializers.CharField(source='pembeli.nama',          read_only=True)
    total         = serializers.SerializerMethodField()
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

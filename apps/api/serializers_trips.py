# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from rest_framework import serializers

from apps.operasional.models import Trip, TripABK
from apps.tangkap.models import HasilTangkap
from apps.penjualan.models import BagiHasil, Penjualan


class TripSerializer(serializers.ModelSerializer):
    kapal_nama       = serializers.CharField(source='kapal.nama_kapal', read_only=True)
    kapal_foto_url   = serializers.SerializerMethodField()
    total_pendapatan = serializers.SerializerMethodField()
    total_biaya      = serializers.SerializerMethodField()

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


class HasilTangkapSerializer(serializers.ModelSerializer):
    jenis_ikan_nama = serializers.CharField(source='jenis_ikan.nama', read_only=True)
    kapal_nama      = serializers.CharField(source='trip.kapal.nama_kapal', read_only=True)
    berat_tersedia  = serializers.ReadOnlyField()

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
        abk  = attrs.get('abk')  or (self.instance.abk  if self.instance else None)
        if trip and abk:
            if not TripABK.objects.filter(trip=trip, abk=abk).exists():
                raise serializers.ValidationError(
                    {'abk': f'ABK "{abk.nama}" tidak terdaftar di trip ini.'})
        return attrs


class TripDetailSerializer(serializers.ModelSerializer):
    """Detail trip lengkap: keuangan + biaya + tangkap + penjualan + ABK."""
    kapal_nama       = serializers.CharField(source='kapal.nama_kapal', read_only=True)
    total_pendapatan = serializers.SerializerMethodField()
    total_biaya      = serializers.SerializerMethodField()
    laba_kotor       = serializers.SerializerMethodField()
    total_bagi_hasil = serializers.SerializerMethodField()
    laba_bersih      = serializers.SerializerMethodField()
    abk_list         = serializers.SerializerMethodField()
    biaya_list       = serializers.SerializerMethodField()
    hasil_tangkap_list = serializers.SerializerMethodField()
    penjualan_list   = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ['id', 'kapal', 'kapal_nama', 'tgl_berangkat', 'tgl_kembali',
                  'status', 'is_laporan_locked', 'catatan',
                  'total_pendapatan', 'total_biaya', 'laba_kotor',
                  'total_bagi_hasil', 'laba_bersih',
                  'abk_list', 'biaya_list', 'hasil_tangkap_list', 'penjualan_list']

    def get_total_pendapatan(self, obj): return float(obj.total_pendapatan())
    def get_total_biaya(self, obj):      return float(obj.total_biaya_operasional())
    def get_laba_kotor(self, obj):       return float(obj.laba_kotor())
    def get_total_bagi_hasil(self, obj): return float(obj.total_bagi_hasil())
    def get_laba_bersih(self, obj):      return float(obj.laba_bersih())

    def get_abk_list(self, obj):
        result = []
        for ta in obj.trip_abk.select_related('abk').all():
            bh = BagiHasil.objects.filter(trip=obj, abk=ta.abk).first()
            result.append({
                'abk_id':       ta.abk.id,
                'abk_nama':     ta.abk.nama,
                'bagi_hasil_id': bh.id if bh else None,
                'nominal':      float(bh.nominal) if bh else None,
                'sudah_dibayar': bh.sudah_dibayar if bh else False,
                'tgl_bayar':    str(bh.tgl_bayar) if bh and bh.tgl_bayar else None,
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
                'id':           b.id,
                'kategori':     b.get_kategori_display(),
                'jumlah':       float(b.jumlah),
                'keterangan':   b.keterangan or '',
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
                'id':             h.id,
                'jenis_ikan':     h.jenis_ikan.nama,
                'berat_kg':       float(h.berat_kg),
                'berat_tersedia': float(h.berat_tersedia),
                'kondisi':        h.get_kondisi_display(),
                'catatan':        h.catatan or '',
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
                'id':            p.id,
                'jenis_ikan':    p.hasil_tangkap.jenis_ikan.nama,
                'pembeli':       p.pembeli.nama,
                'berat_terjual': float(p.berat_terjual),
                'harga_per_kg':  float(p.harga_per_kg),
                'total':         float(p.berat_terjual * p.harga_per_kg),
                'tgl_jual':      str(p.tgl_jual),
                'foto_bukti_url': foto_url,
            })
        return result

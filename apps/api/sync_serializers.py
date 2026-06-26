# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
"""Serializer tulis + helper untuk endpoint sinkronisasi (lihat sync.py)."""
from rest_framework import serializers

from apps.penjualan.models import Penjualan
from apps.tangkap.models import HasilTangkap
from apps.operasional.models import BiayaOperasional


def _rp(v):
    """Format angka jadi 'Rp 1.500.000' (titik ribuan)."""
    try:
        n = int(float(v))
        return f'Rp {n:,}'.replace(',', '.')
    except (TypeError, ValueError):
        return f'Rp {v}'


class PenjualanWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Penjualan
        fields = ['hasil_tangkap', 'pembeli', 'berat_terjual',
                  'harga_per_kg', 'tgl_jual', 'catatan']


class HasilTangkapWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HasilTangkap
        fields = ['trip', 'jenis_ikan', 'berat_kg', 'kondisi', 'catatan']


class BiayaWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiayaOperasional
        fields = ['trip', 'kategori', 'jumlah', 'keterangan']


def _ok(client_uuid, obj, dup=False):
    return {
        'client_uuid': client_uuid,
        'status': 'duplicate' if dup else 'synced',
        'id': obj.id,
        'trip_id': getattr(obj, 'trip_id', None),
    }


def _fail(client_uuid, error):
    return {'client_uuid': client_uuid, 'status': 'failed', 'error': error}


_KAT_LABEL = {
    'bbm': 'BBM',
    'es': 'Es Balok',
    'logistik': 'Logistik',
    'perawatan': 'Perawatan Alat',
    'lainnya': 'Lainnya',
}

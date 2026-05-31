# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.db.models import Sum, F, Count
from apps.operasional.models import Trip
from apps.penjualan.models import Penjualan
from apps.tangkap.models import HasilTangkap

def get_rekap_trip(trip):
    """Kalkulasi lengkap satu trip."""
    pendapatan = Penjualan.objects.filter(
        hasil_tangkap__trip=trip
    ).aggregate(
        total=Sum(F('berat_terjual') * F('harga_per_kg'))
    )['total'] or 0

    biaya = trip.total_biaya_operasional()
    bagi_hasil = trip.total_bagi_hasil()
    laba = trip.laba_bersih()

    total_tangkap = HasilTangkap.objects.filter(
        trip=trip
    ).aggregate(total=Sum('berat_kg'))['total'] or 0

    return {
        'trip': trip,
        'pendapatan': pendapatan,
        'biaya': biaya,
        'bagi_hasil': bagi_hasil,
        'laba': laba,
        'total_tangkap': total_tangkap,
    }

def get_rekap_periode(bulan, tahun):
    """Rekap semua trip dalam satu periode bulan/tahun."""
    trips = Trip.objects.filter(
        tgl_berangkat__month=bulan,
        tgl_berangkat__year=tahun
    ).select_related('kapal')

    data = [get_rekap_trip(t) for t in trips]

    total_pendapatan = sum(d['pendapatan'] for d in data)
    total_biaya = sum(d['biaya'] for d in data)
    total_bagi_hasil = sum(d['bagi_hasil'] for d in data)
    total_laba = sum(d['laba'] for d in data)
    total_tangkap = sum(d['total_tangkap'] for d in data)

    return {
        'data': data,
        'total_pendapatan': total_pendapatan,
        'total_biaya': total_biaya,
        'total_bagi_hasil': total_bagi_hasil,
        'total_laba': total_laba,
        'total_tangkap': total_tangkap,
        'jumlah_trip': len(data),
    }

def get_rekap_per_kapal(tahun):
    """Rekap produktivitas per kapal dalam satu tahun."""
    trips = Trip.objects.filter(
        tgl_berangkat__year=tahun,
        status='selesai'
    ).select_related('kapal')

    kapal_map = {}
    for trip in trips:
        nama = trip.kapal.nama_kapal
        if nama not in kapal_map:
            kapal_map[nama] = {
                'kapal': trip.kapal,
                'jumlah_trip': 0,
                'total_tangkap': 0,
                'total_pendapatan': 0,
                'total_bagi_hasil': 0,
                'total_laba': 0,
            }
        rekap = get_rekap_trip(trip)
        kapal_map[nama]['jumlah_trip'] += 1
        kapal_map[nama]['total_tangkap'] += rekap['total_tangkap']
        kapal_map[nama]['total_pendapatan'] += rekap['pendapatan']
        kapal_map[nama]['total_bagi_hasil'] += rekap['bagi_hasil']
        kapal_map[nama]['total_laba'] += rekap['laba']

    return list(kapal_map.values())
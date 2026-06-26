# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from datetime import date as _date

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from ..models import Trip, BiayaOperasional
from ..forms import BiayaOperasionalForm


@login_required
def operasional_feed(request):
    """Tab Operasional (dock) — feed semua aktivitas (biaya/tangkap/jual) lintas trip."""
    from apps.tangkap.models import HasilTangkap
    from apps.penjualan.models import Penjualan

    tipe = request.GET.get('tipe', 'semua')
    q = request.GET.get('q', '').strip()
    entries = []

    if tipe in ('semua', 'biaya'):
        bq = BiayaOperasional.objects.select_related('trip')
        if q:
            bq = bq.filter(Q(keterangan__icontains=q) | Q(kategori__icontains=q))
        for b in bq:
            tgl = b.dibuat_pada.date() if b.dibuat_pada else b.trip.tgl_berangkat
            entries.append({
                'tipe': 'biaya',
                'judul': b.keterangan or b.get_kategori_display(),
                'tgl': tgl,
                'nilai': b.jumlah,
                'satuan': 'rp',
            })

    if tipe in ('semua', 'tangkap'):
        tq = HasilTangkap.objects.select_related('trip', 'jenis_ikan')
        if q:
            tq = tq.filter(jenis_ikan__nama__icontains=q)
        for h in tq:
            tgl = h.dibuat_pada.date() if h.dibuat_pada else h.trip.tgl_berangkat
            entries.append({
                'tipe': 'tangkap',
                'judul': str(h.jenis_ikan),
                'tgl': tgl,
                'nilai': h.berat_kg,
                'satuan': 'kg',
            })

    if tipe in ('semua', 'jual'):
        jq = Penjualan.objects.select_related('hasil_tangkap__jenis_ikan')
        if q:
            jq = jq.filter(hasil_tangkap__jenis_ikan__nama__icontains=q)
        for p in jq:
            entries.append({
                'tipe': 'jual',
                'judul': str(p.hasil_tangkap.jenis_ikan),
                'tgl': p.tgl_jual,
                'nilai': p.total_nilai(),
                'satuan': 'jual',
            })

    entries.sort(key=lambda e: e['tgl'] or _date.min, reverse=True)

    trip_aktif = Trip.objects.filter(
        status__in=['persiapan', 'berlayar'],
    ).select_related('kapal').order_by('-tgl_berangkat').first()

    # Target trip untuk input biaya: biaya operasional harus SELALU bisa diinput.
    # Utamakan trip aktif; jika tidak ada, pakai trip terbaru yang belum dikunci;
    # terakhir pakai trip terbaru apa pun. Bisa None hanya jika belum ada trip sama sekali.
    trip_biaya = (
        trip_aktif
        or Trip.objects.filter(is_laporan_locked=False).select_related('kapal').order_by('-tgl_berangkat').first()
        or Trip.objects.select_related('kapal').order_by('-tgl_berangkat').first()
    )

    return render(request, 'operasional/feed.html', {
        'entries': entries,
        'tipe': tipe,
        'q': q,
        'trip_aktif': trip_aktif,
        'trip_biaya': trip_biaya,
        'biaya_form': BiayaOperasionalForm(),
    })

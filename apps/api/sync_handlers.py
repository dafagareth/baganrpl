# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
"""SyncHandlersMixin — handler _sync_* per tipe operasi untuk SyncView (lihat sync.py)."""
import base64
import logging
import uuid as _uuid

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction

from apps.penjualan.models import Penjualan
from apps.tangkap.models import HasilTangkap
from apps.operasional.models import BiayaOperasional
from .fcm import notify_owners
from .sync_serializers import (
    PenjualanWriteSerializer, HasilTangkapWriteSerializer, BiayaWriteSerializer,
    _ok, _fail, _rp, _KAT_LABEL,
)

logger = logging.getLogger(__name__)


class SyncHandlersMixin:
    """Handler per-tipe operasi. Mengandalkan self._pengirim (di-set SyncView.post)."""

    def _sync_penjualan(self, client_uuid, data, operator_name):
        existing = Penjualan.objects.filter(client_uuid=client_uuid).first()
        if existing:
            return _ok(client_uuid, existing, dup=True)

        foto_base64 = data.get('foto_bukti_base64')
        data_clean = {k: v for k, v in data.items() if k != 'foto_bukti_base64'}

        serializer = PenjualanWriteSerializer(data=data_clean)
        if not serializer.is_valid():
            return _fail(client_uuid, serializer.errors)
        vd = serializer.validated_data

        try:
            with transaction.atomic():
                ht = HasilTangkap.objects.select_for_update().select_related(
                    'trip__kapal', 'jenis_ikan'
                ).get(pk=vd['hasil_tangkap'].pk)
                if ht.trip.is_laporan_locked:
                    return _fail(client_uuid,
                                 'Penjualan tidak bisa ditambahkan — laporan trip sudah dikunci.')
                tersedia = ht.berat_tersedia
                if vd['berat_terjual'] > tersedia:
                    return _fail(
                        client_uuid,
                        f'Stok tidak cukup! Tersedia {tersedia:g} kg, '
                        f'diminta {vd["berat_terjual"]:g} kg.',
                    )
                obj = Penjualan.objects.create(client_uuid=client_uuid, **vd)

                if foto_base64:
                    try:
                        obj.foto_bukti.save(
                            f'{client_uuid}.jpg',
                            ContentFile(base64.b64decode(foto_base64)),
                            save=True,
                        )
                    except Exception as foto_err:
                        logger.warning('Foto bukti gagal disimpan uuid=%s: %s',
                                       client_uuid, foto_err)
        except IntegrityError:
            existing = Penjualan.objects.filter(client_uuid=client_uuid).first()
            if existing:
                return _ok(client_uuid, existing, dup=True)
            raise

        # Notifikasi kaya detail
        berat = float(vd['berat_terjual'])
        harga = float(vd['harga_per_kg'])
        total = berat * harga
        berat_str = f'{berat:g}'
        kapal = ht.trip.kapal.nama_kapal
        ikan  = ht.jenis_ikan.nama if ht.jenis_ikan else 'ikan'
        notify_owners(
            event='penjualan',
            judul=f'Penjualan — {kapal}',
            pesan=f'{operator_name}: {berat_str} kg {ikan} × {_rp(harga)}/kg = {_rp(total)}',
            data={'trip_id': ht.trip_id},
            pengirim=self._pengirim,
        )
        return _ok(client_uuid, obj)

    def _sync_hasil_tangkap(self, client_uuid, data, operator_name):
        existing = HasilTangkap.objects.filter(client_uuid=client_uuid).first()
        if existing:
            return _ok(client_uuid, existing, dup=True)

        foto_base64 = data.get('foto_bukti_base64')
        data_clean = {k: v for k, v in data.items() if k != 'foto_bukti_base64'}

        serializer = HasilTangkapWriteSerializer(data=data_clean)
        if not serializer.is_valid():
            return _fail(client_uuid, serializer.errors)
        vd = serializer.validated_data
        if vd['trip'].status != 'selesai':
            return _fail(client_uuid,
                         'Hasil tangkap hanya bisa untuk trip yang sudah selesai.')
        if vd['trip'].is_laporan_locked:
            return _fail(client_uuid,
                         'Hasil tangkap tidak bisa ditambahkan — laporan trip sudah dikunci.')

        try:
            obj = HasilTangkap.objects.create(client_uuid=client_uuid, **vd)
            if foto_base64:
                try:
                    obj.foto_bukti.save(
                        f'{client_uuid}.jpg',
                        ContentFile(base64.b64decode(foto_base64)),
                        save=True,
                    )
                except Exception as foto_err:
                    logger.warning('Foto bukti tangkap gagal uuid=%s: %s',
                                   client_uuid, foto_err)
        except IntegrityError:
            existing = HasilTangkap.objects.filter(client_uuid=client_uuid).first()
            if existing:
                return _ok(client_uuid, existing, dup=True)
            raise

        # Notifikasi kaya detail
        berat = float(vd['berat_kg'])
        ikan  = vd['jenis_ikan'].nama if vd.get('jenis_ikan') else 'ikan'
        kondisi = vd.get('kondisi') or ''
        kapal   = vd['trip'].kapal.nama_kapal
        kondisi_str = f' ({kondisi})' if kondisi else ''
        notify_owners(
            event='hasil_tangkap',
            judul=f'Hasil Tangkap — {kapal}',
            pesan=f'{operator_name}: {berat:g} kg {ikan}{kondisi_str}',
            data={'trip_id': obj.trip_id},
            pengirim=self._pengirim,
        )
        return _ok(client_uuid, obj)

    def _sync_tangkap_dan_jual(self, client_uuid, data, operator_name):
        existing_ht = HasilTangkap.objects.filter(client_uuid=client_uuid).first()
        if existing_ht:
            penjualan = Penjualan.objects.filter(
                client_uuid=str(_uuid.uuid5(_uuid.NAMESPACE_OID, f'{client_uuid}_jual'))).first()
            result = _ok(client_uuid, existing_ht, dup=True)
            if penjualan:
                result['penjualan_id'] = penjualan.id
            return result

        foto_base64 = data.get('foto_bukti_base64')
        langsung_jual = bool(data.get('langsung_jual', False))

        ht_data = {k: v for k, v in data.items()
                   if k in ('trip', 'jenis_ikan', 'berat_kg', 'kondisi', 'catatan')}
        ht_ser = HasilTangkapWriteSerializer(data=ht_data)
        if not ht_ser.is_valid():
            return _fail(client_uuid, ht_ser.errors)
        vd_ht = ht_ser.validated_data

        if vd_ht['trip'].status != 'selesai':
            return _fail(client_uuid,
                         'Hasil tangkap hanya bisa untuk trip yang sudah selesai.')
        if vd_ht['trip'].is_laporan_locked:
            return _fail(client_uuid,
                         'Laporan trip sudah dikunci — tidak bisa input data baru.')

        penjualan = None
        try:
            with transaction.atomic():
                ht = HasilTangkap.objects.create(client_uuid=client_uuid, **vd_ht)

                if foto_base64:
                    try:
                        ht.foto_bukti.save(
                            f'{client_uuid}.jpg',
                            ContentFile(base64.b64decode(foto_base64)),
                            save=True,
                        )
                    except Exception as e:
                        logger.warning('Foto tangkap_dan_jual gagal uuid=%s: %s',
                                       client_uuid, e)

                if langsung_jual:
                    jual_data = {
                        'hasil_tangkap': ht.id,
                        'pembeli':        data.get('pembeli'),
                        'berat_terjual':  data.get('berat_terjual'),
                        'harga_per_kg':   data.get('harga_per_kg'),
                        'tgl_jual':       data.get('tgl_jual'),
                        'catatan':        data.get('catatan_jual', ''),
                    }
                    jual_ser = PenjualanWriteSerializer(data=jual_data)
                    if not jual_ser.is_valid():
                        raise ValueError(str(jual_ser.errors))
                    vd_jual = jual_ser.validated_data

                    if vd_jual['berat_terjual'] > vd_ht['berat_kg']:
                        raise ValueError(
                            f"Berat terjual ({vd_jual['berat_terjual']:g} kg) "
                            f"melebihi berat tangkap ({vd_ht['berat_kg']:g} kg)."
                        )
                    penjualan = Penjualan.objects.create(
                        client_uuid=str(_uuid.uuid5(_uuid.NAMESPACE_OID, f'{client_uuid}_jual')), **vd_jual)

        except IntegrityError:
            existing_ht = HasilTangkap.objects.filter(
                client_uuid=client_uuid).first()
            if existing_ht:
                penjualan = Penjualan.objects.filter(
                    client_uuid=str(_uuid.uuid5(_uuid.NAMESPACE_OID, f'{client_uuid}_jual'))).first()
                result = _ok(client_uuid, existing_ht, dup=True)
                if penjualan:
                    result['penjualan_id'] = penjualan.id
                return result
            raise

        # Notifikasi
        berat   = float(vd_ht['berat_kg'])
        ikan    = vd_ht['jenis_ikan'].nama if vd_ht.get('jenis_ikan') else 'ikan'
        kapal   = vd_ht['trip'].kapal.nama_kapal

        if langsung_jual and penjualan:
            harga = float(data.get('harga_per_kg', 0))
            berat_jual = float(data.get('berat_terjual', berat))
            total = berat_jual * harga
            notify_owners(
                event='tangkap_dan_jual',
                judul=f'Tangkap & Jual — {kapal}',
                pesan=f'{operator_name}: {berat:g} kg {ikan} → {_rp(total)}',
                data={'trip_id': ht.trip_id},
                pengirim=self._pengirim,
            )
        else:
            notify_owners(
                event='hasil_tangkap',
                judul=f'Hasil Tangkap — {kapal}',
                pesan=f'{operator_name}: {berat:g} kg {ikan}',
                data={'trip_id': ht.trip_id},
                pengirim=self._pengirim,
            )

        result = _ok(client_uuid, ht)
        if penjualan:
            result['penjualan_id'] = penjualan.id
        return result

    def _sync_biaya(self, client_uuid, data, operator_name):
        existing = BiayaOperasional.objects.filter(client_uuid=client_uuid).first()
        if existing:
            return _ok(client_uuid, existing, dup=True)

        foto_base64 = data.get('foto_bukti_base64')
        data_clean = {k: v for k, v in data.items() if k != 'foto_bukti_base64'}

        serializer = BiayaWriteSerializer(data=data_clean)
        if not serializer.is_valid():
            return _fail(client_uuid, serializer.errors)
        vd = serializer.validated_data

        if vd['trip'].is_laporan_locked:
            return _fail(client_uuid,
                         'Biaya tidak bisa ditambahkan — laporan trip sudah dikunci.')

        try:
            obj = BiayaOperasional.objects.create(client_uuid=client_uuid, **vd)
            if foto_base64:
                try:
                    obj.foto_bukti.save(
                        f'{client_uuid}.jpg',
                        ContentFile(base64.b64decode(foto_base64)),
                        save=True,
                    )
                except Exception as foto_err:
                    logger.warning('Foto bukti biaya gagal uuid=%s: %s',
                                   client_uuid, foto_err)
        except IntegrityError:
            existing = BiayaOperasional.objects.filter(client_uuid=client_uuid).first()
            if existing:
                return _ok(client_uuid, existing, dup=True)
            raise

        # Notifikasi kaya detail
        kat_label = _KAT_LABEL.get(vd['kategori'], vd['kategori'].title())
        jumlah    = float(vd['jumlah'])
        kapal     = vd['trip'].kapal.nama_kapal
        keterangan = (vd.get('keterangan') or '').strip()
        detail = f' — {keterangan}' if keterangan else ''
        notify_owners(
            event='biaya',
            judul=f'Biaya Operasional — {kapal}',
            pesan=f'{operator_name}: {kat_label} {_rp(jumlah)}{detail}',
            data={'trip_id': obj.trip_id},
            pengirim=self._pengirim,
        )
        return _ok(client_uuid, obj)

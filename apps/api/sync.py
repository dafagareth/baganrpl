# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
"""Endpoint sinkronisasi offline (outbox) untuk input operator.

Prinsip:
- Idempoten: setiap operasi punya client_uuid; kiriman ulang tidak menggandakan.
- Server source of truth: validasi (terutama stok) dihitung ulang di server,
  di dalam transaksi.
- Hasil per-item: satu operasi gagal tidak menggagalkan yang lain.
- Notifikasi: per-operasi, kaya detail (jenis, nominal, berat, kapal).

Pemecahan file (tiap < 300 baris):
- sync_serializers.py : serializer tulis + helper (_rp/_ok/_fail/_KAT_LABEL)
- sync_handlers.py    : SyncHandlersMixin berisi handler _sync_* per tipe
- sync.py (ini)       : SyncView — entry point + dispatch per operasi
"""
from rest_framework.response import Response
from rest_framework.views import APIView

from .sync_handlers import SyncHandlersMixin
from .sync_serializers import _fail


class SyncView(SyncHandlersMixin, APIView):
    def post(self, request):
        operations = request.data.get('operations')
        if not isinstance(operations, list):
            return Response({'detail': "'operations' harus berupa list"}, status=400)

        operator_name = request.user.get_full_name() or request.user.username
        self._pengirim = request.user
        results = [self._process(op, operator_name) for op in operations]

        return Response({'results': results})

    def _process(self, op, operator_name):
        client_uuid = (op or {}).get('client_uuid')
        op_type = (op or {}).get('type')
        data = (op or {}).get('data', {})
        if not client_uuid:
            return _fail(client_uuid, 'client_uuid wajib diisi')
        handler = {
            'penjualan':       self._sync_penjualan,
            'hasil_tangkap':   self._sync_hasil_tangkap,
            'biaya':           self._sync_biaya,
            'tangkap_dan_jual': self._sync_tangkap_dan_jual,
        }.get(op_type)
        if handler is None:
            return _fail(client_uuid, f"type tidak dikenal: {op_type}")
        try:
            return handler(client_uuid, data, operator_name)
        except Exception as e:  # jaring pengaman agar 1 item tidak menjatuhkan batch
            return _fail(client_uuid, str(e))

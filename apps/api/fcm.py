# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
"""
Utilitas FCM (Firebase Cloud Messaging) untuk push notification ke owner.

Arsitektur dua lapis:
  1. Notification (DB) → sumber kebenaran, bisa dibaca ulang kapan saja
  2. FCM push          → petunjuk "ada pesan baru", boleh gagal tanpa merusak data

Konfigurasi:
  Set FIREBASE_CREDENTIALS_PATH di .env ke path file JSON service account.
  Kalau tidak ada, FCM dilewati tapi Notification DB tetap dibuat.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_initialized = False

# Import di level modul agar bisa di-mock di test.
# Akan None kalau firebase-admin belum terinstall.
try:
    from firebase_admin import messaging
except ImportError:  # pragma: no cover
    messaging = None  # type: ignore[assignment]

def _init_firebase():
    """Inisialisasi Firebase Admin SDK (idempoten). Return True jika siap."""
    global _initialized
    if _initialized:
        return True

    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
    if not cred_path:
        return False  # FCM belum dikonfigurasi, silent skip

    try:
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(cred_path))
        _initialized = True
        return True
    except Exception as exc:
        logger.error("FCM init gagal: %s", exc)
        return False

def _send_to_tokens(tokens: list[str], title: str, body: str, data: dict | None = None):
    """
    Kirim push ke list FCM token.
    Token kadaluarsa (UnregisteredError) dihapus otomatis dari DB.
    Return (n_sukses, n_gagal).
    """
    if not tokens or not _init_firebase():
        return 0, 0

    from .models import DeviceToken

    sukses = gagal = 0
    str_data = {k: str(v) for k, v in (data or {}).items()}

    for tok in tokens:
        try:
            # `messaging` adalah nama modul yang di-import di atas —
            # ini memungkinkan test mem-mock-nya via patch('apps.api.fcm.messaging')
            messaging.send(messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=str_data,
                token=tok,
            ))
            sukses += 1
        except messaging.UnregisteredError:
            DeviceToken.objects.filter(token=tok).delete()
            logger.info("Token FCM kedaluarsa dihapus: %s…", tok[:16])
            gagal += 1
        except Exception as exc:
            logger.error("FCM send error [%s…]: %s", tok[:16], exc)
            gagal += 1

    return sukses, gagal

def notify_owners(event: str, judul: str, pesan: str, data: dict | None = None,
                  pengirim=None):
    """
    Simpan Notification ke DB **dan** kirim FCM push ke semua device owner.

    Selalu berhasil membuat Notification DB;
    kegagalan FCM hanya di-log, tidak di-raise.

    Return: list Notification yang dibuat.
    """
    from django.contrib.auth import get_user_model
    from .models import DeviceToken, Notification, UserProfile

    User = get_user_model()

    owner_ids = list(
        UserProfile.objects.filter(role='owner').values_list('user_id', flat=True)
    )
    if not owner_ids:
        logger.warning("notify_owners: tidak ada user dengan role owner.")
        return []

    owners = User.objects.filter(id__in=owner_ids)

    notifs = Notification.objects.bulk_create([
        Notification(user=u, event=event, judul=judul, pesan=pesan,
                     pengirim=pengirim)
        for u in owners
    ])

    tokens = list(
        DeviceToken.objects.filter(user_id__in=owner_ids)
        .values_list('token', flat=True)
    )
    n_ok, n_fail = _send_to_tokens(tokens, judul, pesan, data)
    if tokens:
        logger.info("FCM push: %d sukses, %d gagal (dari %d token)",
                    n_ok, n_fail, len(tokens))

    return notifs

# bagan-api

Backend REST API untuk manajemen operasional usaha bagan (perikanan).

Mobile app: [bagan-app](https://github.com/dafaalhafiz/bagan-app) (Flutter Android)

---

## Daftar Isi

- [Gambaran Umum](#gambaran-umum)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Pengguna & Peran](#pengguna--peran)
- [Alur Bisnis](#alur-bisnis)
- [Logika Keuangan](#logika-keuangan)
- [Stack Teknologi](#stack-teknologi)
- [Struktur Proyek](#struktur-proyek)
- [Setup & Menjalankan](#setup--menjalankan)
- [API Endpoints](#api-endpoints)
- [Fitur Offline-First](#fitur-offline-first)
- [Notifikasi Push (FCM)](#notifikasi-push-fcm)
- [Menjalankan Test](#menjalankan-test)

---

## Gambaran Umum

Sistem ini membantu pemilik usaha bagan mengelola operasional armada kapal secara digital — mulai dari pencatatan trip, biaya, hasil tangkap, penjualan ikan, hingga pembayaran bagi hasil ABK.

**Masalah yang diselesaikan:**
- Operator di lapangan sering berada di lokasi tanpa sinyal → butuh input **offline**
- Pemilik usaha perlu memantau kondisi terkini dari HP → butuh **notifikasi push**
- Investor perlu melihat profil usaha → tersedia **landing page publik**

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                         │
│                                                             │
│  ┌──────────────────────┐    ┌───────────────────────────┐  │
│  │   Flutter Android    │    │      Web Browser          │  │
│  │  (Operator + Owner)  │    │  (Investor landing page   │  │
│  │                      │    │   + Laporan web)          │  │
│  │  • Input offline     │    │                           │  │
│  │  • Sync outbox       │    │                           │  │
│  │  • Push notification │    │                           │  │
│  └──────────┬───────────┘    └───────────────────────────┘  │
└─────────────│───────────────────────────────────────────────┘
              │ REST API (JSON + JWT)
              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DJANGO BACKEND                         │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  apps.api   │  │  apps.master │  │ apps.operasional  │   │
│  │  (DRF/JWT)  │  │  (Kapal,ABK) │  │ (Trip, Biaya)    │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ apps.tangkap│  │apps.penjualan│  │  apps.laporan    │   │
│  │(HasilTangkap│  │(Penjualan,   │  │  (Ekspor Excel)  │   │
│  │            )│  │ BagiHasil)   │  │                  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                             │
│                    SQLite Database                          │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│              Firebase Cloud Messaging (FCM)                  │
│         Push notification ke device owner                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Pengguna & Peran

| Peran | Akses | Platform |
|-------|-------|----------|
| **Operator** | Input biaya, hasil tangkap, penjualan (offline) | Flutter Android |
| **Owner** | Dashboard, bagi hasil ABK, notifikasi | Flutter Android |
| **Investor** | Landing page profil usaha (read-only) | Web browser |
| **Admin** | Panel admin Django | Web browser |

---

## Alur Bisnis

```
Master Data
(Kapal, ABK, Jenis Ikan, Pembeli)
        │
        ▼
    TRIP dibuat
    (kapal, tanggal, ABK)
        │
        ├──▶ Biaya Operasional
        │    (BBM, Es, Logistik, dll)
        │
        │    [Trip selesai]
        │         │
        │         ▼
        ├──▶ Hasil Tangkap
        │    (jenis ikan, berat, kondisi)
        │         │
        │         ▼
        ├──▶ Penjualan
        │    (pembeli, berat terjual, harga/kg)
        │         │
        │         ▼
        └──▶ Bagi Hasil ABK
             (nominal, sudah dibayar)
                  │
                  ▼
              Laporan
         (Laba Kotor, Laba Bersih)
```

---

## Logika Keuangan

```
Pendapatan       = Σ (berat_terjual × harga_per_kg)
Biaya            = Σ biaya_operasional per trip
Laba Kotor       = Pendapatan − Biaya
Total Bagi Hasil = Σ nominal bagi hasil yang sudah_dibayar=True
Laba Bersih      = Laba Kotor − Total Bagi Hasil
```

> **Catatan:** Bagi hasil adalah kebijakan pemilik — nominal ditentukan manual oleh owner, tidak otomatis dari persentase laba.

---

## Stack Teknologi

### Backend (Django)
| Komponen | Versi |
|----------|-------|
| Python | 3.14 |
| Django | 6.0.4 |
| Django REST Framework | 3.17.1 |
| SimpleJWT | 5.5.1 |
| python-dotenv | 1.2.2 |
| firebase-admin | latest |
| openpyxl | 3.1.5 (ekspor laporan) |

### Mobile (Flutter)
| Komponen | Versi |
|----------|-------|
| Flutter | 3.44.0 (stable) |
| Dart | ≥3.12.0 |
| flutter_riverpod | 2.6.1 |
| drift (SQLite) | 2.23.1 |
| dio | 5.8.0 |
| go_router | 14.8.1 |
| connectivity_plus | 6.1.4 |

---

## Struktur Proyek

```
PROJECT-Sistem_Informasi_Usaha_Bagan/   ← Django backend
├── apps/
│   ├── api/                 ← REST API (JWT, sync, FCM)
│   │   ├── views.py         ← Semua endpoint API
│   │   ├── serializers.py   ← Serializer DRF
│   │   ├── sync.py          ← Endpoint sinkronisasi offline
│   │   ├── fcm.py           ← Utilitas FCM push notification
│   │   ├── models.py        ← UserProfile, DeviceToken, Notification
│   │   ├── tests_sync.py    ← 10 test sync endpoint
│   │   └── tests_bagi_hasil.py  ← 9 test bagi hasil
│   ├── master/              ← Kapal, ABK, JenisIkan, Pembeli
│   ├── operasional/         ← Trip, BiayaOperasional
│   ├── tangkap/             ← HasilTangkap
│   ├── penjualan/           ← Penjualan, BagiHasil
│   └── laporan/             ← Ekspor Excel, laporan web
├── config/
│   ├── settings.py          ← Konfigurasi dari .env
│   └── urls.py              ← URL routing utama
├── templates/               ← Template HTML (web)
├── static/                  ← CSS, JS
├── .env                     ← SECRET_KEY, DEBUG, FCM path
├── requirements.txt
└── manage.py

bagan_app/                              ← Flutter mobile app
├── lib/
│   ├── main.dart            ← Entry point
│   ├── app.dart             ← Router + BaganApp widget
│   ├── core/
│   │   ├── api/             ← Dio client + JWT interceptor
│   │   ├── auth/            ← Auth state (Riverpod)
│   │   ├── db/              ← SQLite offline (Drift)
│   │   ├── sync/            ← Outbox sync service
│   │   └── theme/           ← Material 3 tema biru laut
│   ├── features/
│   │   ├── auth/            ← Login screen
│   │   ├── operator/        ← Home, Biaya, Tangkap, Penjualan
│   │   └── owner/           ← Dashboard, Trips, BagiHasil, Notifikasi
│   └── shared/
│       └── widgets/         ← StatCard, CurrencyText, TripPicker, SyncFab
├── android/
└── pubspec.yaml
```

---

## Setup & Menjalankan

### Prasyarat
- Python 3.11+
- Flutter 3.44+ (stable channel)
- Android SDK + NDK (untuk build APK)

### Backend Django

```bash
# 1. Clone & masuk ke direktori
cd PROJECT-Sistem_Informasi_Usaha_Bagan

# 2. Buat virtual environment
python -m venv myworld
source myworld/bin/activate          # Linux/Mac
# myworld\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Konfigurasi .env
cp .env.example .env                 # edit sesuai kebutuhan
# Isi: SECRET_KEY, DEBUG, ALLOWED_HOSTS, FIREBASE_CREDENTIALS_PATH

# 5. Migrasi database
python manage.py migrate

# 6. Buat superuser (untuk panel admin)
python manage.py createsuperuser

# 7. Jalankan server
python manage.py runserver 0.0.0.0:8000
```

> Untuk HP fisik: server harus dijalankan dengan `0.0.0.0:8000` agar bisa diakses dari jaringan LAN.

### Flutter App

```bash
cd bagan_app

# 1. Install dependencies
flutter pub get

# 2. Generate Drift database code
dart run build_runner build --delete-conflicting-outputs

# 3. Sesuaikan IP server di lib/core/api/api_client.dart
#    - Emulator Android : http://10.0.2.2:8000/api/
#    - HP fisik via LAN : http://192.168.x.x:8000/api/

# 4. Build APK debug
flutter build apk --debug

# APK ada di: build/app/outputs/flutter-apk/app-debug.apk
```

### Setup Firebase (untuk push notification)

1. Buka [Firebase Console](https://console.firebase.google.com)
2. Buat project → **Project Settings → Service Accounts → Generate new private key**
3. Simpan file JSON ke server, isi path-nya di `.env`:
   ```
   FIREBASE_CREDENTIALS_PATH=/path/ke/firebase-credentials.json
   ```
4. Di Flutter: tambah `google-services.json` ke `android/app/` (dari Firebase Console → Android app)

---

## API Endpoints

Base URL: `http://server:8000/api/`

Semua endpoint (kecuali login) membutuhkan header:
```
Authorization: Bearer <access_token>
```

### Auth
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `auth/login/` | Login, return JWT + role |
| POST | `auth/refresh/` | Refresh access token |
| GET | `me/` | Info user yang login |
| POST | `devices/` | Daftarkan FCM token device |

### Data Referensi (cache offline)
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `kapal/` | Daftar kapal aktif |
| GET | `abk/` | Daftar ABK aktif |
| GET | `jenis-ikan/` | Daftar jenis ikan |
| GET | `pembeli/` | Daftar pembeli |
| GET | `trips/` | Daftar semua trip |
| GET | `trips/{id}/` | Detail trip + ringkasan keuangan |
| GET | `hasil-tangkap/` | Stok ikan tersedia (berat_tersedia > 0) |

### Sinkronisasi Offline
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `sync/` | Kirim batch operasi dari outbox |

**Format request sync:**
```json
{
  "operations": [
    {
      "client_uuid": "uuid-unik-per-operasi",
      "type": "biaya | hasil_tangkap | penjualan",
      "data": { ...field sesuai tipe... }
    }
  ]
}
```

**Format response:**
```json
{
  "results": [
    {"client_uuid": "...", "status": "synced", "id": 42},
    {"client_uuid": "...", "status": "duplicate", "id": 41},
    {"client_uuid": "...", "status": "failed", "error": "Stok tidak cukup"}
  ]
}
```

### Bagi Hasil (Owner Only)
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `trips/{id}/bagi-hasil/` | List bagi hasil trip |
| POST | `trips/{id}/bagi-hasil/` | Tambah bagi hasil (owner) |
| PATCH | `bagi-hasil/{id}/` | Edit nominal / tandai dibayar |
| DELETE | `bagi-hasil/{id}/` | Hapus bagi hasil |

### Lainnya
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `dashboard/` | Ringkasan statistik owner |
| GET | `notifications/` | Inbox notifikasi |

---

## Fitur Offline-First

### Prinsip Dasar
1. **Client UUID** — setiap operasi punya UUID unik, mencegah duplikasi saat dikirim ulang
2. **Outbox pattern** — data disimpan lokal dulu, dikirim saat ada koneksi
3. **Server source of truth** — validasi (stok, trip status) dilakukan di server
4. **Per-item result** — satu operasi gagal tidak membatalkan batch lain

### Skenario Sync
```
[Operator di lapangan, offline]
Input data → Simpan ke SQLite (outbox, status: pending)

[Dapat sinyal]
Tap "Sinkronisasi" → POST /api/sync/ dengan semua pending
Server proses → return per-item result
  ✓ synced   → mark as synced di lokal
  ✓ duplicate → data sudah ada, skip
  ✗ failed   → mark as failed, tampilkan error

[Owner di HP]
Notifikasi push masuk → "3 data baru dari lapangan"
```

---

## Notifikasi Push (FCM)

### Alur
```
Operator sync → POST /api/sync/
                    ↓ (ada yang synced)
              notify_owners()
                    ↓
        ┌─────────────────────┐
        │  Notification (DB)  │  ← inbox /api/notifications/
        └─────────────────────┘
        ┌─────────────────────┐
        │    FCM push         │  ← pop-up di HP owner
        └─────────────────────┘
```

### Graceful Degradasi
- `FIREBASE_CREDENTIALS_PATH` kosong → FCM dilewati, Notification DB tetap dibuat
- Token FCM kadaluarsa → otomatis dihapus dari database

---

## Menjalankan Test

```bash
# Semua test API (25 test)
python manage.py test apps.api

# Per modul
python manage.py test apps.api.tests_sync      # 10 test sync
python manage.py test apps.api.tests_bagi_hasil # 9 test bagi hasil
python manage.py test apps.api.tests_fcm        # 6 test FCM

# Dengan verbosity
python manage.py test apps.api -v 2
```

---

## Variabel Environment (.env)

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Firebase (opsional — FCM tidak aktif jika kosong)
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-service-account.json
```

---

## Lisensi

Proyek akademik — Rekayasa Perangkat Lunak, Semester 4.

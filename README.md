# bagan-api

Backend REST API untuk manajemen operasional usaha bagan (perikanan).
Dibangun dengan Django REST Framework + JWT + Firebase Cloud Messaging.

Mobile app: [bagan-app](https://github.com/dafaalhafiz/bagan-app) (Flutter Android)

---

## Gambaran Singkat

Sistem ini membantu pemilik usaha bagan mengelola operasional armada kapal secara digital — pencatatan trip, biaya, hasil tangkap, penjualan ikan, hingga bagi hasil ABK.

**Masalah yang diselesaikan:**
- Operator di lapangan sering tanpa sinyal → butuh input **offline** di mobile
- Pemilik usaha perlu pantau kondisi dari HP → butuh **notifikasi push**
- Investor perlu lihat profil usaha → tersedia **landing page publik**

---

## Stack

| Komponen | Versi |
|---|---|
| Python | 3.14 |
| Django | 6.0.4 |
| Django REST Framework | 3.17.1 |
| SimpleJWT | 5.5.1 |
| firebase-admin | latest |
| python-dotenv | 1.2.2 |

---

## Struktur

```
apps/
├── api/           ← REST API: endpoint, serializer, sync, FCM, permissions
├── master/        ← Kapal, ABK, JenisIkan, Pembeli
├── operasional/   ← Trip, BiayaOperasional
├── tangkap/       ← HasilTangkap
├── penjualan/     ← Penjualan, BagiHasil
└── laporan/       ← Laporan web + ekspor

config/
├── settings.py    ← Konfigurasi dari .env
└── urls.py

templates/         ← HTML (landing page, laporan web)
static/            ← CSS, JS
```

---

## Setup

```bash
# 1. Clone
git clone https://github.com/dafaalhafiz/bagan-api.git
cd bagan-api

# 2. Virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Konfigurasi environment
cp .env.example .env
# Edit .env — isi SECRET_KEY, DEBUG, ALLOWED_HOSTS

# 5. Migrasi
python manage.py migrate

# 6. Buat akun admin
python manage.py createsuperuser

# 7. Jalankan
python manage.py runserver 0.0.0.0:8000
```

> Gunakan `0.0.0.0:8000` agar bisa diakses dari HP fisik di jaringan yang sama.

---

## Variabel Environment

Lihat `.env.example` untuk template lengkap. Variabel utama:

```env
SECRET_KEY=ganti-dengan-secret-key-kuat
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Firebase — kosongkan jika belum setup (FCM dilewati, DB notification tetap jalan)
FIREBASE_CREDENTIALS_PATH=
```

---

## API Endpoints

Base URL: `http://server:8000/api/`
Semua endpoint butuh header `Authorization: Bearer <access_token>` kecuali login.

### Auth
| Method | Endpoint | Keterangan |
|---|---|---|
| POST | `auth/login/` | Login → JWT + role |
| POST | `auth/refresh/` | Refresh access token |
| GET/PATCH | `me/` | Profil user yang login |
| POST | `auth/change-password/` | Ganti password |
| POST | `devices/` | Daftarkan FCM token |

### Master Data
| Method | Endpoint | Keterangan |
|---|---|---|
| GET/POST | `kapal/` | Daftar + tambah kapal |
| GET/POST | `abk/` | Daftar + tambah ABK |
| GET/POST | `jenis-ikan/` | Daftar + tambah jenis ikan |
| GET/POST | `pembeli/` | Daftar + tambah pembeli |

### Trip & Operasional
| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `trips/` | Semua trip |
| POST | `trips/create/` | Buat trip baru |
| GET | `trips/{id}/` | Detail trip + keuangan |
| PATCH | `trips/{id}/` | Update status trip |
| POST | `trips/{id}/kunci/` | Kunci laporan trip |
| GET/POST | `trips/{id}/bagi-hasil/` | List + tambah bagi hasil |
| PATCH/DELETE | `bagi-hasil/{id}/` | Edit/hapus bagi hasil |

### Sinkronisasi Offline
| Method | Endpoint | Keterangan |
|---|---|---|
| POST | `sync/` | Kirim batch operasi dari outbox mobile |

Format request:
```json
{
  "operations": [
    {
      "client_uuid": "uuid-unik",
      "type": "biaya | hasil_tangkap | penjualan | tangkap_dan_jual",
      "data": { }
    }
  ]
}
```

### Dashboard & Laporan
| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `dashboard/` | Ringkasan statistik owner |
| GET | `laporan/charts/` | Data chart P&L + biaya |
| GET | `armada/charts/` | Fleet utilization + tren |
| GET | `armada/lokasi/` | Titik GPS tiap trip |
| GET | `notifications/` | Inbox notifikasi owner |

---

## Logika Keuangan

```
Pendapatan  = Σ (berat_terjual × harga_per_kg)
Biaya       = Σ biaya_operasional per trip
Laba Kotor  = Pendapatan − Biaya
Laba Bersih = Laba Kotor − Σ bagi_hasil (sudah_dibayar = True)
```

Nominal bagi hasil ditentukan manual oleh owner — tidak otomatis dari persentase.

---

## Offline-First

Setiap operasi dari mobile punya `client_uuid` unik. Server menerima batch via `/api/sync/` dan memproses per-item:

- `synced` → berhasil disimpan
- `duplicate` → UUID sudah ada, skip (idempoten)
- `failed` → validasi gagal (stok kurang, dll), dikembalikan sebagai error

---

## Notifikasi Push (FCM)

Setiap kali operator sync, server kirim push notification ke semua owner via FCM. Jika `FIREBASE_CREDENTIALS_PATH` kosong, push dilewati — inbox notifikasi di database tetap dibuat.

---

## Test

```bash
# Semua test (25 test)
python manage.py test apps.api

# Per modul
python manage.py test apps.api.tests_sync        # 10 test sync
python manage.py test apps.api.tests_bagi_hasil  # 9 test bagi hasil
python manage.py test apps.api.tests_fcm         # 6 test FCM
```

---

## Lisensi

Source Available — lihat file [LICENSE](LICENSE) untuk detail.
Kontak: dafagareth@gmail.com

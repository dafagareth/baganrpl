# Sistem Informasi Usaha Bagan

Aplikasi **web** untuk mengelola operasional usaha bagan (perikanan): pencatatan trip,
biaya, hasil tangkap, penjualan ikan, bagi hasil ABK, sampai laporan keuangan.

Dibangun dengan Django (HTML server-rendered, bukan SPA). Database PostgreSQL (lewat Docker)
atau SQLite (dev lokal).

> Proyek ini awalnya juga punya REST API + app Flutter, tapi yang disetujui & dipakai
> sekarang **fokus web saja**. Kode API tetap disimpan sebagai arsip — lihat
> [Arsip: REST API & Mobile](#arsip-rest-api--mobile).

---

## Gambaran Singkat

Membantu pemilik usaha bagan mengelola armada kapal secara digital. Dua peran, tampilan
menyesuaikan otomatis setelah login:

- **Pemilik (owner)** — dashboard, master data (kapal/ABK/jenis ikan/pembeli), semua laporan, bagi hasil.
- **Operator** — fokus trip miliknya: mulai berlayar, catat biaya, hasil tangkap, dan penjualan.

---

## Fitur

- Pencatatan **Trip** dengan alur status: persiapan → berlayar → selesai
- **Biaya operasional**, **hasil tangkap**, dan **penjualan** (bisa input banyak baris sekaligus)
- **Bagi hasil ABK** — nominal ditentukan manual oleh owner
- **Dashboard** grafik: pendapatan & biaya, laba, top ikan/pembeli, utilisasi armada
- **Laporan** rekap per bulan & per kapal + **ekspor Excel dan PDF**
- **Light & dark mode** dengan palet hangat (cozy, nyaman di mata untuk sesi lama), tampilan **ramah HP** (mobile-friendly), ikon Material Symbols
- Halaman **publik** (landing page) untuk pengunjung

---

## Stack

| Komponen | Versi |
|---|---|
| Python | 3.12 |
| Django | 6.0.4 |
| Database | PostgreSQL 16 (Docker) / SQLite (dev lokal) |
| WhiteNoise | sajikan file statis di gunicorn |
| Gunicorn | server WSGI (produksi/Docker) |

---

## Struktur

```
apps/
├── core/         ← peran (owner/operator), login, dashboard, halaman publik
├── master/       ← Kapal, ABK, JenisIkan, Pembeli
├── operasional/  ← Trip, TripABK, BiayaOperasional (views sebagai paket views/)
├── tangkap/      ← HasilTangkap
├── penjualan/    ← Penjualan, BagiHasil
├── laporan/      ← laporan web + ekspor Excel/PDF
└── api/          ← arsip REST API + UserProfile (peran). API nonaktif, lihat bawah.

config/
├── settings.py   ← konfigurasi dari .env (DB otomatis Postgres/SQLite)
└── urls.py

templates/        ← HTML (web admin + landing page), dipecah per partial
static/css/       ← tokens.css (warna/tema) + base, layout/, components/, pages/
```

---

## Jalankan dengan Docker (disarankan)

```bash
cp .env.example .env          # isi SECRET_KEY, DEBUG, ALLOWED_HOSTS
docker compose up --build
```

Buka **http://localhost:8000**. Saat start, container otomatis menjalankan `migrate` dan
`collectstatic`, lalu gunicorn. Data PostgreSQL tersimpan permanen di volume `pg_data`.

```bash
docker compose up -d      # jalankan di belakang layar
docker compose logs -f web
docker compose down       # hentikan
```

---

## Jalankan Lokal (tanpa Docker)

```bash
# 1. Virtual environment
python -m venv myworld
source myworld/bin/activate          # Windows: myworld\Scripts\activate

# 2. Install dependency
pip install -r requirements.txt

# 3. Konfigurasi
cp .env.example .env                 # isi SECRET_KEY, DEBUG, ALLOWED_HOSTS

# 4. Migrasi (otomatis pakai SQLite)
python manage.py migrate

# 5. Buat akun admin
python manage.py createsuperuser

# 6. Jalankan
python manage.py runserver
```

Tersedia juga `Makefile`: `make run`, `make migrate`, `make migrations`, `make test`, `make static`.

---

## Data Dummy (Demo)

Mengisi data contoh realistis (kapal, ABK, trip mingguan, hasil tangkap, penjualan,
bagi hasil) sekaligus membuat akun demo:

```bash
python manage.py seed_dummy --flush
# di Docker:
docker compose exec web python manage.py seed_dummy --flush
```

`--flush` menghapus dulu semua data operasional & master (akun lama tidak dihapus).
Command ini membuat dua akun demo:

| Peran | Username | Password |
|---|---|---|
| Pemilik (owner) | `owner` | `owner` |
| Operator | `operator` | `operator` |

> Akun di atas hanya untuk demo. **Ganti password-nya** sebelum dipakai di produksi nyata.

---

## Variabel Environment

Lihat `.env.example`. Variabel utama:

```env
SECRET_KEY=ganti-dengan-secret-key-kuat
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Password PostgreSQL untuk Docker (default: bagan123). Dev lokal pakai SQLite, abaikan.
DB_PASSWORD=bagan123
```

Database dipilih otomatis: ada env `POSTGRES_DB` (di Docker) → PostgreSQL, selain itu → SQLite.

---

## Logika Keuangan

```
Pendapatan  = Σ (berat_terjual × harga_per_kg)
Biaya       = Σ biaya_operasional per trip
Laba Kotor  = Pendapatan − Biaya
Laba Bersih = Laba Kotor − Σ bagi_hasil
```

Nominal bagi hasil ditentukan manual oleh owner — tidak otomatis dari persentase.

---

## Arsip: REST API & Mobile

Folder `apps/api/` berisi REST API (Django REST Framework + JWT), sinkronisasi offline,
dan FCM push yang dulu dipakai app Flutter
[bagan-app](https://github.com/dafagareth/bagan_app).

API ini **dinonaktifkan** (di-comment di `config/urls.py`, `config/settings.py`, dan
`requirements.txt`) karena proyek fokus web. Yang **tetap dipakai** dari app ini hanya
model `UserProfile` (peran owner/operator) + signal pembuat profil otomatis.

Mengaktifkan kembali (bila mobile dilanjut): uncomment baris terkait di ketiga file di atas,
lalu `pip install djangorestframework djangorestframework-simplejwt django-cors-headers`.

---

## Lisensi

Source Available — lihat file [LICENSE](LICENSE).
Kontak: dafagareth@gmail.com

# Dokumentasi Belajar Kode — Sistem Informasi Usaha Bagan

Catatan ini untuk **memahami kode sendiri**, terutama buat persiapan demo / live coding.
Urutan baca yang disarankan dari atas ke bawah.

| File | Isi |
|------|-----|
| [01-arsitektur-dan-alur.md](01-arsitektur-dan-alur.md) | Apa itu Django, pola MVT, struktur folder, alur sebuah request dari URL sampai halaman tampil. |
| [02-model-database.md](02-model-database.md) | Semua tabel (model), relasinya, dan istilah seperti ForeignKey / on_delete / related_name. |
| [03-views-form-url.md](03-views-form-url.md) | Beda function view vs class view, view bawaan Django, form, validasi, dan routing URL. |
| [04-fitur-dan-aturan-bisnis.md](04-fitur-dan-aturan-bisnis.md) | Peran owner/operator, alur status trip, bagi hasil, laporan, dan middleware demo. |
| [05-sintaks-python-django.md](05-sintaks-python-django.md) | Contekan sintaks Python & Django yang dipakai di project ini. |
| [06-skenario-live-coding.md](06-skenario-live-coding.md) | Latihan: "pindahkan ini ke sini", "tambah field", "jelaskan baris ini", lengkap dengan langkahnya. |

---

## Cara menjalankan project (lokal)

```bash
# 1. aktifkan virtualenv yang sudah ada
source myworld/bin/activate          # (di project ini foldernya bernama myworld/)

# 2. siapkan database (lokal pakai SQLite otomatis)
python manage.py migrate

# 3. isi data contoh + akun demo (owner/owner, operator/operator)
python manage.py seed_dummy --flush

# 4. jalankan server
python manage.py runserver
# buka http://127.0.0.1:8000/
```

Perintah lain yang sering dipakai:

```bash
python manage.py check               # cek error konfigurasi/kode tanpa menjalankan server
python manage.py makemigrations      # bikin file migrasi setelah mengubah model
python manage.py migrate             # terapkan perubahan struktur tabel ke database
python manage.py createsuperuser     # bikin akun admin untuk /admin/
python manage.py shell               # terminal Python dengan Django sudah siap
```

## Peta cepat: file mana untuk apa

```
config/            # pengaturan project (settings, daftar URL utama)
  settings.py      # konfigurasi: app terpasang, database, middleware, dll
  urls.py          # "papan saklar" URL teratas, menyambung ke tiap app

apps/              # kode fitur, dipisah per modul
  core/            # perekat: login, dashboard, halaman publik, role, filter Rupiah
  master/          # data acuan: kapal, ABK, jenis ikan, pembeli
  operasional/     # Trip (inti) + biaya + ABK per trip
  tangkap/         # hasil tangkap
  penjualan/       # penjualan + bagi hasil ABK
  laporan/         # rekap & ekspor Excel/PDF
  api/             # REST API untuk mobile — NONAKTIF (lihat catatan di bawah)

templates/         # file HTML (tampilan)
static/            # CSS, JS, gambar
```

> **Catatan soal `apps/api`:** itu sisa rencana aplikasi mobile (Flutter) yang
> sekarang **tidak dipakai** — route-nya dimatikan di `config/urls.py`. Fokus sistem
> ada di versi web. Jadi kalau dosen minta live coding, hampir pasti di app web
> (core, master, operasional, tangkap, penjualan, laporan), bukan di `api`.

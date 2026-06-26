# 01 — Arsitektur & Alur

## Apa itu Django?

Django itu *framework* web untuk Python. Maksudnya: kerangka kerja yang sudah
menyediakan banyak hal siap pakai (database, form, login, halaman admin), jadi kita
tinggal menulis bagian logikanya saja.

## Pola MVT (Model - View - Template)

Django memakai pola **MVT**. Tiga lapisan yang harus kamu bedakan:

| Lapisan | Tugas | Di project ini |
|---------|-------|----------------|
| **Model** | Bentuk data + aturannya. Satu model = satu tabel di database. | `apps/*/models.py` |
| **View** | Otak/logika: menerima request, ambil/olah data, tentukan respons. | `apps/*/views.py` |
| **Template** | Tampilan HTML yang dilihat user. | `templates/` |

Kalau di kuliah kamu belajar MVC, MVT itu mirip: "View" Django = Controller, "Template"
Django = View. Yang penting paham: **logika ada di views.py, tampilan ada di templates/.**

## Alur satu request (penting untuk dijelaskan ke dosen)

Misal user buka `http://situs/operasional/trip/`:

```
1. Browser kirim request URL  ──►  config/urls.py
2. config/urls.py melihat awalan "operasional/" lalu melempar ke apps/operasional/urls.py
3. apps/operasional/urls.py mencocokkan "trip/" ──► memanggil TripListView
4. TripListView (di apps/operasional/views/trip.py):
      - ambil data Trip dari database (lewat Model)
      - siapkan data untuk ditampilkan
5. View memilih template 'operasional/trip_list.html'
6. Template diisi data, jadi HTML
7. HTML dikirim balik ke browser  ──►  halaman tampil
```

Satu kalimat untuk dihafal:
**"URL menentukan view mana yang jalan; view mengambil data lewat model lalu merendernya ke template."**

## Struktur folder & tugas tiap app

Project dipecah jadi beberapa *app* (modul). Tiap app fokus ke satu urusan:

- **core** — hal umum: login, dashboard owner, halaman publik, pengecekan peran
  (owner/operator), filter Rupiah, middleware demo.
- **master** — data acuan yang dipakai berulang: Kapal, ABK, Jenis Ikan, Pembeli.
- **operasional** — **inti aplikasi**: Trip (sekali melaut), ABK yang ikut, dan biaya.
- **tangkap** — Hasil Tangkap (ikan yang didapat dalam trip).
- **penjualan** — Penjualan hasil tangkap + Bagi Hasil ABK.
- **laporan** — rekap bulanan/per kapal + ekspor Excel & PDF.
- **api** — REST API mobile, **nonaktif** (diabaikan saja).

### Isi standar sebuah app

Tiap app punya file dengan tugas tetap:

```
apps/operasional/
  models.py     # definisi tabel (Trip, TripABK, BiayaOperasional)
  views/        # logika halaman (di app lain biasanya cukup views.py satu file)
  forms.py      # definisi form input + validasinya
  urls.py       # daftar URL khusus app ini
  admin.py      # daftar model yang muncul di halaman /admin/
  apps.py       # konfigurasi nama app (jarang disentuh)
  migrations/   # riwayat perubahan struktur tabel (dibuat otomatis)
```

> Di app `operasional`, `views.py` sudah dipecah jadi **folder** `views/` berisi
> `feed.py`, `trip.py`, `biaya.py`, `abk.py`. Bagi Django itu tetap dianggap satu
> "views" karena ada `__init__.py` yang mengumpulkan semuanya. Lihat
> `apps/operasional/views/__init__.py`.

## Settings & URL utama

- `config/settings.py` — semua konfigurasi. Yang sering ditanya:
  - `INSTALLED_APPS` = daftar app yang aktif.
  - `MIDDLEWARE` = lapisan yang dilewati tiap request (keamanan, sesi, dll).
  - `DATABASES` = pakai PostgreSQL kalau ada env Docker, kalau tidak SQLite (dev lokal).
  - `TEMPLATES` > `context_processors` = fungsi yang menyuntik variabel ke semua template
    (di sini `apps.core.context_processors.user_role` yang bikin `is_owner` tersedia di mana saja).
- `config/urls.py` — daftar URL teratas. Tiap `include('apps.X.urls')` menyambungkan
  ke daftar URL milik app X.

Lanjut: [02-model-database.md](02-model-database.md)

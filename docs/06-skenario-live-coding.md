# 06 — Skenario Live Coding

Latihan untuk perintah yang sering dilontarkan dosen. Tiap skenario ada **langkah**
dan **yang perlu dicek**. Selalu jalankan `python manage.py check` setelah mengubah kode.

---

## A. "Pindahkan bagian ini ke file/tempat lain"

Contoh: dosen minta fungsi `is_owner` dipindah, atau sebuah view dipindah ke file lain.

**Prinsip:** memindahkan kode = potong dari tempat lama, tempel di tempat baru, lalu
**perbaiki import** di semua file yang memakainya.

Langkah:
1. Pindahkan potongan kode ke file tujuan.
2. Di file tujuan, pastikan `import`-nya ada (mis. butuh `from django.db import models`).
3. Di file lama (dan file lain yang memakai), ubah import jadi menunjuk lokasi baru.
4. `python manage.py check` → harus bersih.

Contoh nyata di project ini: `apps/operasional/views/` tadinya satu file `views.py`,
lalu dipecah jadi `trip.py`, `biaya.py`, `abk.py`, `feed.py`. Supaya `urls.py` tetap
jalan tanpa diubah, semua kelas dikumpulkan lagi di `views/__init__.py`:
```python
from .trip import TripListView, TripDetailView, ...
```
Pola "kumpulkan di `__init__.py`" inilah yang membuat `from . import views` di urls.py
tetap menemukan semuanya.

> Tip cepat: kalau setelah pindah muncul error `ImportError` / `cannot import name`,
> berarti tinggal benahi baris `import`-nya. Itu error paling umum saat memindah kode.

---

## B. "Tambah satu field/kolom baru ke model"

Contoh: tambah `cuaca` ke Trip, atau `email` ke Pembeli.

Langkah (urut, jangan dibalik):
1. **Tambah field di model** (`apps/operasional/models.py`):
   ```python
   cuaca = models.CharField(max_length=50, blank=True, null=True)
   ```
2. **Bikin migrasi** (Django mendeteksi perubahan model):
   ```bash
   python manage.py makemigrations
   ```
3. **Terapkan ke database**:
   ```bash
   python manage.py migrate
   ```
4. **Tampilkan/izinkan input** kalau perlu: tambahkan nama field ke `fields = [...]`
   di form terkait (`apps/operasional/forms.py`), lalu tampilkan di template.

> Kenapa butuh migrasi? Karena mengubah model = mengubah struktur tabel. `makemigrations`
> bikin "resep" perubahan, `migrate` menjalankannya ke database. Ini pertanyaan klasik dosen.

---

## C. "Jelaskan baris ini"

Cara membaca baris apa pun: pecah dari kiri ke kanan. Contoh baris dari `KapalListView`:

```python
qs = super().get_queryset().annotate(jml_trip=Count('trips')).order_by('nama_kapal')
```

Baca jadi: "ambil data standar (`super().get_queryset()`), lalu **tambah** kolom hitungan
jumlah trip tiap kapal (`annotate(... Count('trips'))`), lalu **urutkan** berdasarkan nama."

Contoh lain (`Trip.total_pendapatan`):
```python
Penjualan.objects.filter(hasil_tangkap__trip=self).aggregate(
    total=Sum(F('berat_terjual') * F('harga_per_kg')))['total'] or 0
```
"Ambil semua Penjualan yang trip-nya = trip ini, lalu minta database menjumlahkan
(berat × harga) tiap baris, ambil hasilnya; kalau kosong pakai 0."

Kalau ditanya baris yang kamu tidak hafal, **jelaskan polanya** (lihat
[05-sintaks-python-django.md](05-sintaks-python-django.md)) — itu sudah cukup.

---

## D. "Tambah aturan validasi"

Contoh: harga jual tidak boleh di bawah `harga_minimum` jenis ikan.

Tempatnya di method `clean()` form (`apps/penjualan/forms.py`):
```python
def clean(self):
    cleaned_data = super().clean()
    ht = cleaned_data.get('hasil_tangkap')
    harga = cleaned_data.get('harga_per_kg')
    if ht and harga is not None:
        minimum = ht.jenis_ikan.harga_minimum
        if minimum and harga < minimum:
            raise forms.ValidationError(
                f'Harga di bawah minimum (Rp {minimum:,.0f}/kg).'
            )
    return cleaned_data
```
Pola: ambil nilai dari `cleaned_data`, cek kondisinya, `raise forms.ValidationError(...)`
kalau melanggar. Ini langsung jalan tanpa migrasi (validasi itu logika, bukan struktur tabel).

---

## E. "Tambah halaman / menu baru" (alur singkat)

Empat langkah, ingat urutannya: **view → url → template → menu**.
1. **View** di `apps/.../views.py` (paling cepat pakai `TemplateView` atau `ListView`).
2. **URL** di `apps/.../urls.py`: `path('alamat/', views.ViewBaru.as_view(), name='nama')`.
3. **Template** HTML di `templates/...` (biasanya `{% extends 'base.html' %}`).
4. **Tautan** menu di `templates/base.html` pakai `{% url 'app:nama' %}`.

---

## F. Jebakan umum saat live coding (hafalin biar tenang)

- **Lupa migrasi** setelah ubah model → error "no such column". Solusi: `makemigrations` + `migrate`.
- **Salah/lupa import** setelah pindah kode → `ImportError`. Solusi: betulkan baris `import`.
- **Indentasi Python** harus konsisten (4 spasi). Campur tab & spasi = `IndentationError`.
- **Lupa `{% csrf_token %}`** di dalam `<form method="post">` → error 403 saat submit.
- **`get()` vs `filter()`**: `get()` error kalau data tidak ada/lebih dari satu; `filter()`
  selalu aman (mengembalikan kumpulan, bisa kosong). Untuk satu objek yang mungkin tak ada,
  pakai `.filter(...).first()` atau `get_object_or_404(...)`.
- **Nama URL salah** → `NoReverseMatch`. Cek `name=` di urls.py dan `app_name`.
- Selalu tutup dengan `python manage.py check`, lalu refresh browser.

---

## Kalimat pembuka kalau diminta menjelaskan project

> "Ini aplikasi web Django dengan pola MVT. Datanya di `models.py`, logika halaman di
> `views.py`, tampilan di `templates/`. Ada dua peran, owner dan operator. Operator
> mencatat trip, biaya, hasil tangkap, dan penjualan dari lapangan; owner memantau lewat
> dashboard, mengatur bagi hasil, dan mengunci laporan. Angka keuangan seperti laba tidak
> disimpan sebagai kolom, tapi dihitung dari data transaksi supaya selalu konsisten."

Itu sudah merangkum 80% pertanyaan pembuka.

# 04 — Fitur & Aturan Bisnis

Ini "kenapa"-nya sistem, bukan sekadar sintaks. Bagian ini paling enak buat ditanya
dosen soal logika usaha.

## Dua peran: owner & operator

- **Owner (pemilik)** — lihat dashboard, kelola data master, atur bagi hasil, kunci laporan, lihat laporan.
- **Operator** — orang lapangan: bikin trip, input ABK, biaya, hasil tangkap, penjualan.

Cara kerjanya:
- Peran disimpan di `User.profile.role` (model `UserProfile`).
- Helper `is_owner(user)` di `apps/core/mixins.py` mengeceknya.
- View khusus owner memakai `OwnerRequiredMixin`. Operator yang nyasar ke halaman owner
  tidak dikasih error 403 mentah, tapi dialihkan ke daftar trip dengan pesan.
- Saat login (`CustomLoginView.get_success_url`): owner → `/dashboard/`, operator → `/operasional/trip/`.
- `is_owner` tersedia di **semua template** lewat context processor
  (`apps/core/context_processors.py`), jadi tombol owner-only bisa disembunyikan dengan
  `{% if is_owner %}`.

## Alur status Trip

```
persiapan ──(Mulai Berlayar)──► berlayar ──(Kapal Kembali)──► selesai ──(Kunci)──► terkunci
   │
   └─ bisa juga dibatalkan ──► batal
```

Aturan yang ditegakkan di kode (`apps/operasional/views/trip.py`):
- **persiapan → berlayar**: harus ada minimal 1 ABK dulu (`TripBerlayarView`).
- **berlayar → selesai**: `TripSelesaiView`, sekalian isi `tgl_kembali`.
- **Hasil tangkap** baru boleh diinput **setelah trip selesai** (dicek di `HasilTangkapCreateView.dispatch`).
- **Kunci laporan** (`TripLockView`, owner saja): set `is_laporan_locked = True`.
  Setelah terkunci, biaya/tangkap/penjualan/ABK **tidak bisa diubah** (kecuali admin/superuser).
- Satu kapal tidak boleh punya dua trip aktif sekaligus (dicek di `TripForm.clean`).

## Stok hasil tangkap & penjualan

- Tiap `HasilTangkap` punya `berat_kg`. Saat dijual, `berat_terjual` mengurangi stok.
- Sisa stok = `HasilTangkap.berat_tersedia` (property di model tangkap).
- `PenjualanForm` cuma menampilkan ikan yang masih ada stok dan **menolak** jual melebihi
  stok (di `clean()`). Jadi tidak mungkin menjual ikan lebih banyak dari yang ditangkap.

## Bagi hasil ABK

Keputusan desain penting (sering ditanya):
- Nominal bagi hasil **ditentukan manual oleh owner**, **bukan** otomatis dari persen laba.
  Alasannya: di usaha bagan, pembagian ke kru itu kebijakan pemilik dan tidak selalu
  proporsional terhadap laba.
- Satu ABK hanya boleh dapat satu baris bagi hasil per trip (`unique_together`), dan
  hanya ABK yang **ikut trip** yang bisa diberi jatah (divalidasi di `BagiHasilForm`).
- Di perhitungan laba, yang dihitung cuma bagi hasil yang **sudah dibayar**
  (`total_bagi_hasil` memfilter `sudah_dibayar=True`).

## Laporan & ekspor

- `apps/laporan/utils.py` punya fungsi murni: `get_rekap_trip` (1 trip),
  `get_rekap_periode` (1 bulan), `get_rekap_per_kapal` (1 tahun).
- Halaman laporan (`LaporanIndexView`) memanggil util itu lalu menampilkannya.
- Ekspor: `ExportExcelView` (file .xlsx via openpyxl) dan `ExportPDFTripView`
  (file .pdf via ReportLab). Keduanya mengirim file sebagai unduhan lewat `HttpResponse`
  dengan header `Content-Disposition: attachment`.

## Middleware "jendela demo"

File `apps/core/middleware.py` → `DemoWindowMiddleware`.

- **Middleware** = lapisan yang dilewati **setiap** request sebelum sampai ke view.
- Fungsinya: kalau env `DEMO_OPEN_UNTIL` sudah lewat (mis. `2026-06-24 12:30` WIB),
  pengunjung publik dapat halaman "Demo ditutup" (HTTP 503) alih-alih situs penuh.
- Ada jalan pintas: buka `?buka=KUNCI` (env `DEMO_BYPASS_KEY`) untuk tetap masuk.
- Dipakai supaya saat demo selesai, situs publik tidak diakses sembarang orang.

## Format tampilan

- Filter Rupiah & tanggal Indonesia ada di `apps/core/templatetags/format_tags.py`:
  `{{ angka|rupiah }}` → `Rp 1.400.000`, `{{ tgl|tgl_indo }}` → `24/06/2026`.
- Nama bulan: `apps/laporan/templatetags/laporan_filters.py` → `{{ 6|nama_bulan }}` → `Juni`.

Lanjut: [05-sintaks-python-django.md](05-sintaks-python-django.md)

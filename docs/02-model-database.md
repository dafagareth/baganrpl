# 02 — Model & Database

Satu **model** = satu **tabel** di database. Satu baris tabel = satu objek.
Field model = kolom tabel. File: `apps/*/models.py`.

## Peta relasi antar tabel (ringkas)

```
        Kapal ──< Trip >── dibuat_oleh ─ User
                   │
        ┌──────────┼─────────────┬─────────────┐
        │          │             │             │
     TripABK   BiayaOperasional  │          BagiHasil ──> ABK
        │                        │
       ABK                  HasilTangkap ──> JenisIkan
                                 │
                             Penjualan ──> Pembeli
```

Bacaan tanda `──<` = "satu ke banyak". Contoh: satu **Kapal** punya banyak **Trip**;
satu **Trip** punya banyak **HasilTangkap**; satu **HasilTangkap** bisa punya banyak
**Penjualan** (dijual sebagian-sebagian).

## Istilah relasi (sering ditanya dosen)

```python
kapal = models.ForeignKey(Kapal, on_delete=models.PROTECT, related_name='trips')
```

- **ForeignKey** = relasi "banyak ke satu". Banyak Trip menunjuk ke satu Kapal.
  Di tabel, ini jadi kolom `kapal_id`.
- **on_delete** = apa yang terjadi kalau data yang ditunjuk (Kapal) dihapus:
  - `PROTECT` = **larang** menghapus Kapal selama masih dipakai Trip (jaga histori).
  - `CASCADE` = ikut terhapus. Contoh: Trip dihapus → BiayaOperasional & TripABK-nya ikut hilang.
  - `SET_NULL` = kolomnya dikosongkan. Contoh: User dihapus → `Trip.dibuat_oleh` jadi kosong, tapi Trip tetap ada.
- **related_name** = nama untuk "akses balik". Karena `related_name='trips'`, dari
  objek kapal kita bisa tulis `kapal.trips.all()` untuk ambil semua trip kapal itu.

Istilah field lain:
- `CharField(max_length=..)` teks pendek; `TextField` teks panjang.
- `DecimalField` angka pecahan presisi (uang/berat) — bukan `FloatField` biar tidak ada pembulatan aneh.
- `BooleanField` true/false. `DateField` tanggal. `DateTimeField` tanggal+jam.
- `null=True` boleh kosong di database; `blank=True` boleh kosong di form. Sering dipakai berdua.
- `choices=[...]` membatasi isi ke pilihan tertentu (mis. status trip).
- `auto_now_add=True` otomatis diisi waktu objek pertama dibuat.

## Daftar model per app

### master (`apps/master/models.py`)
- **Kapal** — perahu bagan. Field penting: `nama_kapal`, `jenis`, `kapasitas`, `status` (aktif/nonaktif/perbaikan).
- **ABK** — anak buah kapal (kru). `nama`, `no_hp`, `aktif`.
- **JenisIkan** — jenis ikan. `nama`, `harga_minimum` (batas jual termurah, dipakai validasi).
- **Pembeli** — pembeli hasil tangkap.
- **OperatorKapal** — tabel penugasan: operator mana pegang kapal mana.

### operasional (`apps/operasional/models.py`)
- **Trip** — sekali melaut. `kapal`, `tgl_berangkat`, `tgl_kembali`, `status`, `is_laporan_locked`.
- **TripABK** — penghubung Trip ↔ ABK (siapa saja yang ikut). `unique_together` mencegah ABK dobel di satu trip.
- **BiayaOperasional** — pengeluaran trip (BBM, es, dll). `kategori`, `jumlah`, `keterangan`.

### tangkap (`apps/tangkap/models.py`)
- **HasilTangkap** — ikan hasil tangkap. `jenis_ikan`, `berat_kg`, `kondisi`.
  - Punya `@property berat_tersedia` = `berat_kg` dikurangi total yang sudah terjual. Dipakai supaya tidak jual melebihi stok.

### penjualan (`apps/penjualan/models.py`)
- **Penjualan** — sebagian/seluruh HasilTangkap dijual ke Pembeli. `berat_terjual`, `harga_per_kg`.
  - `total_nilai()` = `berat_terjual * harga_per_kg`.
- **BagiHasil** — jatah uang per ABK dari sebuah trip. `nominal` (diisi manual owner), `sudah_dibayar`.

## Method hitung di model Trip (wajib paham)

Ada di `apps/operasional/models.py`. Ini **bukan kolom**, tapi fungsi yang dihitung saat dipanggil:

```python
def total_biaya_operasional(self):     # jumlah semua biaya trip ini
def total_pendapatan(self):            # jumlah (berat_terjual x harga_per_kg) semua penjualan trip
def laba_kotor(self):                  # pendapatan - biaya
def total_bagi_hasil(self):            # jumlah bagi hasil yang SUDAH dibayar
def laba_bersih(self):                 # laba_kotor - total_bagi_hasil
```

Konsep kunci di sini: **aggregate**. Daripada mengambil semua baris lalu menjumlah di
Python (lambat), kita minta database yang menjumlahkan:

```python
self.biaya_operasional.aggregate(total=models.Sum('jumlah'))['total'] or 0
```

- `self.biaya_operasional` — akses balik (related_name) ke semua biaya milik trip ini.
- `aggregate(total=Sum('jumlah'))` — suruh DB jumlahkan kolom `jumlah`, hasil disebut `total`.
- `['total']` — ambil nilainya. `or 0` — kalau belum ada data (None), pakai 0.

Untuk perkalian antar-kolom dipakai `F()`:

```python
Sum(F('berat_terjual') * F('harga_per_kg'))
```

`F('namakolom')` artinya "nilai kolom ini di tiap baris", supaya perkaliannya
dikerjakan oleh database baris per baris.

## Soal "tidak perlu dinormalisasi" dari dosen

Yang dosen maksud: untuk tugas ini **tidak wajib memaksakan bentuk normal (1NF/2NF/3NF)
secara teoretis di ERD/class diagram**. Misalnya boleh saja menyimpan nilai turunan
atau menggabungkan hal yang secara teori bisa dipisah, asal desainnya jelas dan jalan.

Tapi sebenarnya desain ini **sudah cukup rapi/ter-normalisasi**: data acuan (Kapal, ABK,
JenisIkan, Pembeli) dipisah ke tabelnya sendiri dan dihubungkan lewat ForeignKey, bukan
diketik ulang di tiap baris. Nilai uang seperti laba **tidak disimpan** sebagai kolom,
melainkan **dihitung saat dibutuhkan** (lihat method di atas) supaya tidak ada data ganda
yang bisa jadi tidak sinkron. Jadi kalau ditanya: "ERD saya sudah memisah entitas master
dan transaksi, relasinya pakai foreign key, dan angka turunan dihitung di kode bukan
disimpan, jadi tidak ada redundansi."

Lanjut: [03-views-form-url.md](03-views-form-url.md)

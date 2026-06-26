# 05 — Contekan Sintaks Python & Django

Contekan cepat sintaks yang muncul di project ini. Tujuannya: pas live coding kamu
tidak bingung "ini maksudnya apa".

## Python dasar

```python
# Variabel & tipe
nama = "KM Anugrah"        # teks (string)
jumlah = 15                # bilangan bulat (int)
harga = 1500.50            # pecahan (float)
aktif = True               # boolean (True/False)
data = None                # "kosong"/belum ada nilai

# f-string: sisipkan nilai ke dalam teks pakai { }
print(f"Kapal {nama} punya {jumlah} trip")   # Kapal KM Anugrah punya 15 trip

# List (daftar) dan dict (kamus pasangan kunci:nilai)
ikan = ["tongkol", "teri"]
trip = {"kapal": "KM Anugrah", "status": "selesai"}
trip["status"]             # ambil nilai -> "selesai"
```

### Fungsi (`def`)
```python
def laba(pendapatan, biaya):    # def = bikin fungsi
    return pendapatan - biaya   # return = nilai yang dikeluarkan

hasil = laba(100, 30)           # panggil fungsi -> 70
```

### Percabangan & perulangan
```python
if status == 'selesai':
    ...
elif status == 'berlayar':
    ...
else:
    ...

for trip in daftar_trip:        # ulangi tiap item
    print(trip)
```

### List comprehension (bikin list ringkas)
```python
# versi panjang
hasil = []
for t in trips:
    hasil.append(get_rekap_trip(t))

# versi ringkas (dipakai di laporan/utils.py)
hasil = [get_rekap_trip(t) for t in trips]
```

### try / except (tangani error)
```python
try:
    value = Decimal(str(value))
except (ValueError, TypeError):
    return value     # kalau gagal, jangan crash; lakukan plan B
```

## Class (kelas) & OOP

```python
class Trip(models.Model):       # class = cetakan objek; (models.Model) = mewarisi dari Model
    status = models.CharField(...)   # atribut

    def laba_bersih(self):      # method = fungsi di dalam class
        return self.laba_kotor() - self.total_bagi_hasil()
```

- **self** = objek itu sendiri. Lewat `self` kita akses atribut/method objek yang sama.
- **`__init__`** = method yang jalan saat objek dibuat (mis. di form, untuk membatasi pilihan).
- **Pewarisan**: `class KapalListView(OwnerRequiredMixin, ListView)` artinya kelas ini
  mewarisi sifat dari `OwnerRequiredMixin` dan `ListView`.
- **`super()`** = panggil versi asli (dari kelas induk) sebelum/sesudah kita tambah sesuatu:
  ```python
  def get_context_data(self, **kwargs):
      ctx = super().get_context_data(**kwargs)   # ambil context standar dulu
      ctx['q'] = ...                              # baru tambah punya kita
      return ctx
  ```
- **`*args, **kwargs`** = "terima argumen sebanyak apa pun". Sering muncul di method yang
  cuma meneruskan argumen ke `super()`.

### Dekorator (`@`)
Tanda `@sesuatu` di atas fungsi/method = "bungkus dengan perilaku tambahan".
```python
@login_required            # wajib login dulu sebelum fungsi jalan
def operasional_feed(request): ...

@property                  # method dipanggil tanpa kurung: ht.berat_tersedia
def berat_tersedia(self): ...

@register.filter           # daftarkan sebagai filter template
def rupiah(value): ...
```

## ORM Django (cara bicara ke database tanpa SQL)

`NamaModel.objects` adalah pintu ke tabelnya.

```python
Kapal.objects.all()                         # ambil semua kapal
Kapal.objects.filter(status='aktif')        # yang statusnya aktif (bisa lebih dari satu)
Kapal.objects.get(pk=5)                      # ambil SATU berdasarkan id (error kalau tak ada)
Trip.objects.filter(...).first()            # ambil satu pertama, atau None kalau kosong
Kapal.objects.count()                        # hitung jumlah baris
Trip.objects.create(kapal=k, ...)            # buat + simpan baris baru
trip.save()                                  # simpan perubahan objek
trip.save(update_fields=['status'])          # simpan kolom tertentu saja (lebih hemat)
```

Filter lanjutan (pakai garis bawah ganda `__`):
```python
.filter(nama__icontains='ang')               # mengandung 'ang' (huruf besar/kecil diabaikan)
.filter(tgl_berangkat__month=6)              # ikuti bagian tanggal
.filter(status__in=['persiapan','berlayar']) # termasuk salah satu dari list
.filter(trip__kapal__nama_kapal='X')         # ikuti relasi antar tabel
```

Gabungan kondisi & agregasi:
```python
from django.db.models import Q, Sum, F, Count
.filter(Q(a__icontains=q) | Q(b__icontains=q))      # | = ATAU, & = DAN
.aggregate(total=Sum('jumlah'))['total']            # jumlahkan satu kolom (1 angka)
.annotate(jml=Count('trips'))                       # tambah kolom hitungan per baris
Sum(F('berat_terjual') * F('harga_per_kg'))         # operasi antar-kolom di DB
.select_related('kapal')                            # ikut ambil data relasi (hindari query berulang)
.values('jenis_ikan__nama').annotate(t=Sum('berat_kg'))  # group-by + jumlah
```

## Sintaks template (file HTML di `templates/`)

```django
{{ variabel }}                       {# tampilkan nilai #}
{{ trip.laba_bersih|rupiah }}        {# pakai filter #}
{% if is_owner %} ... {% endif %}    {# logika #}
{% for t in trip_list %} ... {% endfor %}
{% url 'operasional:trip_detail' trip.id %}   {# buat link dari nama URL #}
{% include 'operasional/trip_detail/header.html' %}   {# sisipkan file lain #}
{% extends 'base.html' %}            {# pakai kerangka induk #}
{% block content %} ... {% endblock %}
{% csrf_token %}                     {# wajib di dalam <form method="post"> #}
```

Lanjut: [06-skenario-live-coding.md](06-skenario-live-coding.md)

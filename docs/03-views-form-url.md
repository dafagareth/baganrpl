# 03 — Views, Form, & URL

## Dua gaya view

### 1. Function-Based View (FBV) — view berupa fungsi
Contoh: `operasional_feed` di `apps/operasional/views/feed.py`,
`penjualan_multi_create` di `apps/penjualan/views.py`.

```python
@login_required                      # dekorator: wajib login dulu
def penjualan_multi_create(request): # 'request' = info request yang masuk
    if request.method == 'POST':     # user mengirim form?
        ... proses simpan ...
        return redirect('penjualan:list')
    ... tampilkan form kosong ...
    return render(request, 'template.html', {'formset': formset})
```

Pola umum form di FBV: **GET = tampilkan form, POST = proses data**.

### 2. Class-Based View (CBV) — view berupa kelas
Kebanyakan view di project ini CBV, mewarisi kelas "generic" bawaan Django supaya
kode jadi singkat. Contoh `KapalListView` di `apps/master/views.py`.

| Kelas generic | Untuk | Yang wajib disebut |
|---------------|-------|--------------------|
| `ListView` | halaman daftar | `model`, `template_name` |
| `DetailView` | halaman detail 1 objek | `model`, `template_name` |
| `CreateView` | form tambah | `model`/`form_class`, `template_name`, tujuan sukses |
| `UpdateView` | form edit | sama seperti Create |
| `DeleteView` | konfirmasi hapus | `model`, `template_name` |
| `TemplateView` | halaman statis/olahan sendiri | `template_name` |

## Method "hook" di CBV (sering dipakai & ditanya)

Kamu tidak menulis ulang semuanya, cukup **menimpa** method yang perlu:

- `get_queryset(self)` — atur **data apa** yang ditampilkan ListView (mis. tambah pencarian).
  Lihat `KapalListView.get_queryset` (pakai `Q()` + `__icontains`).
- `get_context_data(self, **kwargs)` — **kirim variabel tambahan** ke template
  (mis. kata kunci `q`, atau `total_pendapatan`).
- `form_valid(self, form)` — jalan **saat data form valid**; tempat menambah data sebelum simpan,
  mis. `form.instance.trip_id = ...` di `HasilTangkapCreateView`.
- `get_form_kwargs(self)` — **titip data ke form** saat dibuat, mis. kirim `trip` ke
  `PenjualanForm` supaya pilihan ikannya dibatasi (`PenjualanCreateForTripView`).
- `dispatch(self, request, ...)` — jalan **paling awal**; dipakai sebagai "satpam"
  (cek syarat, kalau gagal redirect). Lihat `HasilTangkapCreateView.dispatch`
  yang menolak input kalau trip belum selesai / sudah dikunci.
- `get_success_url(self)` — ke mana setelah berhasil simpan.

## Mixin (potongan kelas yang ditempel)

```python
class KapalListView(OwnerRequiredMixin, ListView):
```

Kelas ini mewarisi DUA hal: `OwnerRequiredMixin` (aturan akses) + `ListView` (perilaku daftar).
- `LoginRequiredMixin` (bawaan) — wajib login.
- `OwnerRequiredMixin` (buatan kita, di `apps/core/mixins.py`) — wajib login **dan** harus owner;
  kalau operator nyasar ke sini, dikasih pesan lalu dilempar ke daftar trip.
- `SuccessMessageMixin` — otomatis munculkan notifikasi sukses (`success_message`).

Urutan penulisan mixin penting: yang kiri "membungkus" yang kanan.

## Form

File `apps/*/forms.py`. Mayoritas **ModelForm**: form yang field-nya otomatis dari model.

```python
class HasilTangkapForm(forms.ModelForm):
    class Meta:
        model = HasilTangkap
        fields = ['jenis_ikan', 'berat_kg', ...]   # field yang boleh diisi
        widgets = { 'jenis_ikan': forms.Select(attrs={'class': 'form-select'}), ... }
```

- `fields = '__all__'` artinya semua field model (lihat `KapalForm`).
- `widgets` cuma mengatur tampilan input (kelas Bootstrap, tipe input), bukan logika.

### Dua tempat mengatur logika form
1. **`__init__`** — membatasi pilihan saat form dibuat. Contoh `PenjualanForm.__init__`
   cuma menampilkan ikan yang stoknya masih ada; `TripABKForm.__init__` cuma menampilkan
   ABK yang belum masuk trip.
2. **`clean()`** — validasi terakhir yang melibatkan beberapa field. Contoh `PenjualanForm.clean`
   menolak kalau `berat_terjual > stok`. Cara menolak: `raise forms.ValidationError("pesan")`.

### Formset = banyak form sekaligus

```python
PenjualanFormSet = forms.modelformset_factory(Penjualan, form=PenjualanMultiForm, extra=1)
```

Dipakai untuk input banyak baris dalam satu halaman (mis. tambah beberapa biaya / bagi
hasil sekaligus). `extra=1` = sediakan satu baris kosong.

## URL & routing

`config/urls.py` (teratas) menyambung ke tiap app:

```python
path('operasional/', include('apps.operasional.urls')),
```

Lalu `apps/operasional/urls.py`:

```python
app_name = 'operasional'
urlpatterns = [
    path('trip/', views.TripListView.as_view(), name='trip_list'),
    path('trip/<int:pk>/', views.TripDetailView.as_view(), name='trip_detail'),
]
```

- `path('trip/<int:pk>/', ...)` — `<int:pk>` menangkap angka dari URL (mis. `/trip/5/`)
  dan mengirimnya ke view sebagai `pk=5`.
- `.as_view()` — wajib untuk CBV (mengubah kelas jadi fungsi yang bisa dipanggil URL).
- `name='trip_detail'` — nama URL. Dipakai supaya tidak menulis alamat manual:
  - di Python: `reverse('operasional:trip_detail', kwargs={'pk': 5})` atau `redirect('operasional:trip_detail', pk=5)`
  - di template: `{% url 'operasional:trip_detail' trip.id %}`
  - format namanya: `namaapp:namaurl`.

Lanjut: [04-fitur-dan-aturan-bisnis.md](04-fitur-dan-aturan-bisnis.md)

# Panduan Deploy — Sistem Informasi Usaha Bagan

Deploy ke **VPS Debian/Ubuntu** pakai Docker Compose (sudah ada) + **Cloudflare Tunnel**
(HTTPS otomatis, tanpa membuka port). Cocok untuk demo ~1 bulan. Estimasi: VPS
~Rp40–90k/bln + domain `.my.id` ~Rp10–15k/thn. Domain: **bagan.my.id**.

Kenapa Cloudflare Tunnel (bukan Caddy/Nginx): `cloudflared` membuat koneksi **keluar**
ke Cloudflare, jadi port 80/443 tidak perlu dibuka. Aman dipakai di VPS bersama
(mis. VPS teman) karena tidak menyentuh web server lain yang mungkin sudah berjalan,
dan satu tunnel bisa melayani banyak domain sekaligus.

## 0. Sebelum mulai
- Punya VPS (Debian 12 / Ubuntu 22.04+), akses SSH sebagai user dengan sudo.
- Domain `bagan.my.id` sudah dipindah ke **Cloudflare**: nameserver di registrar
  diarahkan ke Cloudflare dan status zone sudah **Active**. Tidak perlu mengatur
  A record manual — tunnel membuat record DNS-nya otomatis (lihat langkah 6).
- Repo sudah ada di GitHub.

## 1. Login & paket dasar
```bash
ssh user@IP_VPS
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ufw
```

## 2. Firewall (cukup SSH)
```bash
sudo ufw allow OpenSSH
sudo ufw enable     # port 80/443/8000 TIDAK perlu dibuka — tunnel pakai koneksi keluar
```

## 3. Install Docker + Compose
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker   # agar bisa docker tanpa sudo
```

## 4. Ambil kode & siapkan .env
```bash
git clone https://github.com/<user>/<repo>.git app && cd app
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # untuk SECRET_KEY
nano .env
```
Isi `.env`:
```
SECRET_KEY=<hasil generate di atas>
DEBUG=False
ALLOWED_HOSTS=bagan.my.id
CSRF_TRUSTED_ORIGINS=https://bagan.my.id
SECURE_SSL_REDIRECT=False
DB_PASSWORD=<password kuat>
```

## 5. Jalankan aplikasi
```bash
docker compose up -d --build          # migrate + collectstatic + gunicorn (127.0.0.1:8000)
docker compose exec web python manage.py seed_dummy --flush   # isi data dummy + akun demo
```
App hanya mendengar di `127.0.0.1:8000` (lihat `docker-compose.yml`), jadi tidak
terekspos langsung ke internet — hanya `cloudflared` di host yang sama yang mengaksesnya.
Nama project Docker dipatok `bagan` (top-level `name:` di compose) agar tidak bentrok
bila VPS dipakai aplikasi lain.

Akun demo: **owner / owner** dan **operator / operator**. Buat admin (opsional):
```bash
docker compose exec web python manage.py createsuperuser
```

## 6. Cloudflare Tunnel = HTTPS otomatis

### 6a. Install cloudflared
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
```

### 6b. Login & buat tunnel
```bash
cloudflared tunnel login                 # buka URL yang muncul, pilih zona bagan.my.id
cloudflared tunnel create bagan          # menghasilkan <TUNNEL-ID> + file kredensial JSON
cloudflared tunnel route dns bagan bagan.my.id     # auto-buat DNS record (CNAME) di Cloudflare
```

### 6c. Konfigurasi ingress
Buat `~/.cloudflared/config.yml`:
```yaml
tunnel: <TUNNEL-ID>
credentials-file: /home/<user>/.cloudflared/<TUNNEL-ID>.json
ingress:
  - hostname: bagan.my.id
    service: http://localhost:8000
  # Contoh menambah domain kedua di VPS yang sama (app lain di port lain):
  # - hostname: domain-lain.com
  #   service: http://localhost:8001
  - service: http_status:404
```

### 6d. Jalankan sebagai service (otomatis nyala saat boot)
```bash
sudo cloudflared --config /home/<user>/.cloudflared/config.yml service install
sudo systemctl enable --now cloudflared
sudo systemctl status cloudflared      # pastikan "active (running)"
```

### 6e. Pengaturan di dashboard Cloudflare
- **SSL/TLS → Overview**: mode **Full**.
- **SSL/TLS → Edge Certificates → Always Use HTTPS**: **On**.

Buka `https://bagan.my.id` — sertifikat TLS dari Cloudflare langsung aktif.

> Alternatif tanpa CLI: buat tunnel lewat **Zero Trust → Networks → Tunnels**,
> jalankan perintah install ber-token yang diberikan, lalu tambah **Public Hostname**
> `bagan.my.id → http://localhost:8000`. DNS record dibuat otomatis.

## 7. Update versi (sekali tarik dari GitHub)
```bash
cd app && git pull && docker compose up -d --build
```

## Catatan keamanan
- `DEBUG=False` di produksi → halaman error tidak membocorkan detail.
- `SECRET_KEY`, `DB_PASSWORD` hanya di `.env` (tidak masuk git).
- Cookie session/CSRF `Secure`, HSTS, nosniff, X-Frame-Options aktif otomatis saat `DEBUG=False`.
  Cloudflare mengirim `X-Forwarded-Proto: https`, dan `SECURE_PROXY_SSL_HEADER` di
  `settings.py` membuat Django mengenali koneksi sebagai HTTPS.
- App di-bind ke `127.0.0.1:8000` + firewall hanya SSH → tidak ada port aplikasi yang publik.
- **Ganti password akun demo** (owner/operator) bila dipakai serius — ini kredensial lemah untuk demo.
- Static via WhiteNoise; media (upload foto) dilayani Django (cukup untuk demo).

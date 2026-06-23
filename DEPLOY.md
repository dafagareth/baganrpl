# Panduan Deploy — Sistem Informasi Usaha Bagan

Deploy ke **VPS Debian/Ubuntu** pakai Docker Compose (sudah ada) + Caddy (HTTPS otomatis).
Cocok untuk demo ~1 bulan. Estimasi: VPS ~Rp40–90k/bln + domain `.my.id`/`.biz.id` ~Rp10–15k/thn.

## 0. Sebelum mulai
- Punya VPS (Debian 12 / Ubuntu 22.04+), akses SSH sebagai user dengan sudo.
- Domain sudah dibeli; arahkan **A record** ke IP VPS (mis. `namadomain.my.id` → `1.2.3.4`).
- Repo sudah ada di GitHub.

## 1. Login & paket dasar
```bash
ssh user@IP_VPS
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ufw
```

## 2. Firewall (penting)
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable          # port 8000 TIDAK dibuka → hanya Caddy (80/443) yang publik
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
ALLOWED_HOSTS=namadomain.my.id
CSRF_TRUSTED_ORIGINS=https://namadomain.my.id
DB_PASSWORD=<password kuat>
```

## 5. Jalankan aplikasi
```bash
docker compose up -d --build          # migrate + collectstatic + gunicorn :8000 (loopback)
docker compose exec web python manage.py seed_dummy --flush   # isi data dummy + akun demo
```
Akun demo: **owner / owner** dan **operator / operator**. Buat admin (opsional):
```bash
docker compose exec web python manage.py createsuperuser
```

## 6. Caddy = HTTPS otomatis
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy

sudo cp Caddyfile /etc/caddy/Caddyfile   # edit domainnya dulu
sudo nano /etc/caddy/Caddyfile           # ganti namadomain.my.id
sudo systemctl reload caddy
```
Buka `https://namadomain.my.id` — sertifikat TLS terbit otomatis.

## 7. Update versi (sekali tarik dari GitHub)
```bash
cd app && git pull && docker compose up -d --build
```

## Catatan keamanan
- `DEBUG=False` di produksi → halaman error tidak membocorkan detail.
- `SECRET_KEY`, `DB_PASSWORD` hanya di `.env` (tidak masuk git).
- Cookie session/CSRF `Secure`, HSTS, nosniff, X-Frame-Options aktif otomatis saat `DEBUG=False`.
- Port 8000 tidak publik (ufw); akses hanya via Caddy (443).
- **Ganti password akun demo** (owner/operator) bila dipakai serius — ini kredensial lemah untuk demo.
- Static via WhiteNoise; media (upload foto) dilayani Django (cukup untuk demo).

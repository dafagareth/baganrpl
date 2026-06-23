# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
"""Middleware jendela demo: tutup akses publik setelah waktu tertentu.

Dikontrol lewat env:
- DEMO_OPEN_UNTIL : "YYYY-MM-DD HH:MM" (waktu lokal Asia/Jakarta). Kosong = selalu buka.
- DEMO_BYPASS_KEY : kata kunci opsional. Buka `https://domain/?buka=KUNCI` sekali untuk
                    melewati penutupan (disimpan di session) — berguna untuk pemilik demo.
"""
import datetime
import zoneinfo

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone

_CLOSED_HTML = """<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Demo ditutup — Usaha Bagan</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
         font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
         background:#0b1f3a; color:#e8eef7; padding:24px; }}
  .box {{ max-width:440px; text-align:center; }}
  .ico {{ font-size:48px; margin-bottom:12px; }}
  h1 {{ font-size:1.5rem; font-weight:600; margin:0 0 10px; }}
  p {{ font-size:15px; line-height:1.6; color:#aebfd6; margin:0 0 8px; }}
  .small {{ font-size:13px; color:#7f93b0; margin-top:18px; }}
</style></head>
<body><div class="box">
  <div class="ico">⚓</div>
  <h1>Demo sedang ditutup</h1>
  <p>Sesi demo <strong>Sistem Informasi Usaha Bagan</strong> sudah berakhir.</p>
  <p>Terima kasih sudah mencoba. Silakan hubungi pemilik bila ingin melihat lagi.</p>
  <div class="small">© 2026 Usaha Bagan</div>
</div></body></html>
"""


def _cutoff():
    raw = (getattr(settings, 'DEMO_OPEN_UNTIL', '') or '').strip()
    if not raw:
        return None
    try:
        naive = datetime.datetime.strptime(raw, '%Y-%m-%d %H:%M')
    except ValueError:
        return None
    tz = zoneinfo.ZoneInfo(getattr(settings, 'TIME_ZONE', 'UTC'))
    return naive.replace(tzinfo=tz)


class DemoWindowMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cutoff = _cutoff()
        if cutoff is not None and timezone.now() > cutoff:
            # Jalur bypass untuk pemilik demo.
            key = (getattr(settings, 'DEMO_BYPASS_KEY', '') or '').strip()
            if key and request.GET.get('buka') == key:
                request.session['demo_bypass'] = True
            if not request.session.get('demo_bypass'):
                return HttpResponse(_CLOSED_HTML, status=503)
        return self.get_response(request)

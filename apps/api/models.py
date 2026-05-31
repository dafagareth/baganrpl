# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('operator', 'Operator'),
        ('owner', 'Pemilik Usaha'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operator')
    foto = models.ImageField(upload_to='profil/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class DeviceToken(models.Model):
    """FCM registration token milik sebuah perangkat/pengguna."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
    )
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, default='android')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.token[:12]}…"

class Notification(models.Model):
    """Inbox notifikasi tersimpan di server (sumber kebenaran, push hanya petunjuk)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    pengirim = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='notifikasi_dikirim',
        null=True, blank=True,
    )
    event = models.CharField(max_length=50, blank=True)
    judul = models.CharField(max_length=150)
    pesan = models.TextField(blank=True)
    dibaca = models.BooleanField(default=False)
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-dibuat']

    def __str__(self):
        return f"{self.judul} -> {self.user.username}"

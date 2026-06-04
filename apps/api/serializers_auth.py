# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import DeviceToken, Notification


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login JWT yang sekaligus mengembalikan role & username."""

    def validate(self, attrs):
        data = super().validate(attrs)
        profile = getattr(self.user, 'profile', None)
        data['role'] = profile.role if profile else None
        data['username'] = self.user.username
        return data


class MeSerializer(serializers.Serializer):
    username  = serializers.CharField()
    nama      = serializers.CharField(allow_blank=True)
    role      = serializers.CharField()
    is_staff  = serializers.BooleanField()
    foto_url  = serializers.CharField(allow_null=True)


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['token', 'platform']
        # Hapus UniqueValidator bawaan DRF — view pakai update_or_create,
        # token yang sama boleh di-update ke user lain (ganti HP / re-login).
        extra_kwargs = {'token': {'validators': []}}


class NotificationSerializer(serializers.ModelSerializer):
    pengirim_nama     = serializers.SerializerMethodField()
    pengirim_foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'event', 'judul', 'pesan', 'dibaca', 'dibuat',
                  'pengirim_nama', 'pengirim_foto_url']

    def get_pengirim_nama(self, obj):
        if not obj.pengirim:
            return None
        return obj.pengirim.get_full_name() or obj.pengirim.username

    def get_pengirim_foto_url(self, obj):
        if not obj.pengirim:
            return None
        profile = getattr(obj.pengirim, 'profile', None)
        if not profile or not profile.foto:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(profile.foto.url) if request else profile.foto.url

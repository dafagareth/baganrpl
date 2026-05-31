# Copyright (c) 2026 Dafa Al Hafiz. MIT License.
from django.contrib import admin

from .models import UserProfile, DeviceToken, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'updated_at')
    search_fields = ('user__username',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('judul', 'user', 'event', 'dibaca', 'dibuat')
    list_filter = ('dibaca', 'event')
    search_fields = ('judul', 'user__username')

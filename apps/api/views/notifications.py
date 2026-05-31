# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import DeviceToken, Notification
from ..serializers import DeviceTokenSerializer, NotificationSerializer


class RegisterDeviceView(APIView):
    """Simpan/refresh FCM token milik pengguna (upsert by token).
    Bersihkan token lama — simpan maksimal 3 token terbaru per user.
    """

    _MAX_TOKENS = 3

    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        platform = serializer.validated_data.get('platform', 'android')
        obj, _ = DeviceToken.objects.update_or_create(
            token=token,
            defaults={'user': request.user, 'platform': platform},
        )

        keep_ids = list(
            DeviceToken.objects.filter(user=request.user)
            .order_by('-id')
            .values_list('id', flat=True)[:self._MAX_TOKENS]
        )
        DeviceToken.objects.filter(user=request.user).exclude(id__in=keep_ids).delete()

        return Response(DeviceTokenSerializer(obj).data, status=status.HTTP_200_OK)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationsReadView(APIView):
    """Tandai semua notifikasi milik user sebagai sudah dibaca."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            user=request.user, dibaca=False
        ).update(dibaca=True)
        return Response({'marked': updated})

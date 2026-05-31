# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from ..serializers import RoleTokenObtainPairSerializer, MeSerializer

User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = RoleTokenObtainPairSerializer


def _me_data(user, request=None):
    profile = getattr(user, 'profile', None)
    foto_url = None
    if profile and profile.foto:
        foto_url = (request.build_absolute_uri(profile.foto.url)
                    if request else profile.foto.url)
    return {
        'username': user.username,
        'nama': user.first_name or '',
        'role': profile.role if profile else None,
        'is_staff': user.is_staff,
        'foto_url': foto_url,
    }


class MeView(APIView):
    def get(self, request):
        return Response(MeSerializer(_me_data(request.user, request)).data)

    def patch(self, request):
        user = request.user
        username = request.data.get('username')
        nama = request.data.get('nama')
        if username is not None:
            username = username.strip()
            if not username:
                return Response({'error': 'Username tidak boleh kosong.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if User.objects.exclude(pk=user.pk).filter(username__iexact=username).exists():
                return Response({'error': 'Username sudah dipakai pengguna lain.'},
                                status=status.HTTP_400_BAD_REQUEST)
            user.username = username
        if nama is not None:
            user.first_name = nama.strip()
        user.save()
        return Response(MeSerializer(_me_data(user, request)).data)


class MeFotoView(APIView):
    """POST: upload foto profil. DELETE: hapus foto."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        foto = request.FILES.get('foto')
        if not foto:
            return Response({'detail': 'File foto wajib dikirim.'}, status=400)
        profile, _ = request.user.profile.__class__.objects.get_or_create(
            user=request.user)
        if profile.foto:
            profile.foto.delete(save=False)
        profile.foto.save(foto.name, foto, save=True)
        return Response(MeSerializer(_me_data(request.user, request)).data)

    def delete(self, request):
        profile = getattr(request.user, 'profile', None)
        if profile and profile.foto:
            profile.foto.delete(save=True)
        return Response(status=204)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_pw = request.data.get('old_password', '').strip()
        new_pw = request.data.get('new_password', '').strip()

        if not old_pw or not new_pw:
            return Response(
                {'error': 'old_password dan new_password wajib diisi.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(new_pw) < 8:
            return Response(
                {'error': 'Password baru minimal 8 karakter.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.check_password(old_pw):
            return Response(
                {'error': 'Password lama tidak tepat.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_pw)
        request.user.save()
        return Response({'message': 'Password berhasil diubah.'})

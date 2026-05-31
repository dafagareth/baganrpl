# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.master.models import Kapal, OperatorKapal
from apps.operasional.models import TripABK
from ..permissions import IsOwner
from ..models import UserProfile

User = get_user_model()

def _operator_data(user):
    profile = getattr(user, 'profile', None)
    kapal_ids = OperatorKapal.objects.filter(operator=user).values_list(
        'kapal__id', 'kapal__nama_kapal'
    )
    return {
        'id': user.id,
        'username': user.username,
        'nama': user.get_full_name() or '',
        'role': profile.role if profile else 'operator',
        'kapal_assigned': [{'id': k[0], 'nama_kapal': k[1]} for k in kapal_ids],
    }

class OperatorAccountListCreateView(APIView):
    """
    GET  /api/accounts/          — list semua akun operator
    POST /api/accounts/          — buat akun operator baru
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        users = User.objects.filter(profile__role='operator').select_related('profile')
        return Response([_operator_data(u) for u in users])

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()
        nama     = request.data.get('nama', '').strip()

        if not username or not password:
            return Response(
                {'detail': 'username dan password wajib diisi.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(password) < 6:
            return Response(
                {'detail': 'Password minimal 6 karakter.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {'detail': 'Username sudah dipakai.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        first, *rest = (nama.split(' ', 1) + [''])[:2]
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first,
            last_name=rest[0] if rest else '',
        )
        # Profile mungkin sudah dibuat otomatis oleh signal post_save —
        # pastikan ada & role-nya operator.
        UserProfile.objects.update_or_create(
            user=user, defaults={'role': 'operator'},
        )
        return Response(_operator_data(user), status=status.HTTP_201_CREATED)

class OperatorAccountDetailView(APIView):
    """
    DELETE /api/accounts/{id}/                  — hapus akun operator
    POST   /api/accounts/{id}/reset-password/   — reset password operator
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def _get_operator(self, pk):
        user = get_object_or_404(User, pk=pk)
        profile = getattr(user, 'profile', None)
        if not profile or profile.role != 'operator':
            return None, Response(
                {'detail': 'Hanya akun operator yang bisa dikelola.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return user, None

    def delete(self, request, pk):
        user, err = self._get_operator(pk)
        if err:
            return err
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        profile = getattr(user, 'profile', None)
        if not profile or profile.role != 'operator':
            return Response(
                {'detail': 'Hanya akun operator yang bisa direset.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        password = request.data.get('password', '').strip()
        if len(password) < 6:
            return Response(
                {'detail': 'Password minimal 6 karakter.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(password)
        user.save(update_fields=['password'])
        return Response({'detail': 'Password berhasil direset.'})

class KapalOperatorView(APIView):
    """
    GET    /api/kapal/{id}/operators/           — list operator di kapal ini
    POST   /api/kapal/{id}/operators/           — assign operator ke kapal
    DELETE /api/kapal/{id}/operators/{uid}/     — cabut operator dari kapal
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, pk):
        kapal = get_object_or_404(Kapal, pk=pk)
        assignments = OperatorKapal.objects.filter(kapal=kapal).select_related(
            'operator__profile'
        )
        data = []
        for a in assignments:
            u = a.operator
            data.append({
                'id': u.id,
                'username': u.username,
                'nama': u.get_full_name() or '',
            })
        return Response(data)

    def post(self, request, pk):
        kapal = get_object_or_404(Kapal, pk=pk)
        uid = request.data.get('operator_id')
        if not uid:
            return Response(
                {'detail': 'operator_id wajib diisi.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = get_object_or_404(User, pk=uid)
        profile = getattr(user, 'profile', None)
        if not profile or profile.role != 'operator':
            return Response(
                {'detail': 'User bukan operator.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _, created = OperatorKapal.objects.get_or_create(operator=user, kapal=kapal)
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({'detail': 'Operator ditugaskan.' if created else 'Sudah ditugaskan.'}, status=code)

    def delete(self, request, pk, uid):
        kapal = get_object_or_404(Kapal, pk=pk)
        user  = get_object_or_404(User, pk=uid)
        deleted, _ = OperatorKapal.objects.filter(operator=user, kapal=kapal).delete()
        if not deleted:
            return Response({'detail': 'Penugasan tidak ditemukan.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ABKTersediaView(APIView):
    """
    GET /api/abk/tersedia/?trip_id=<id>

    Mengembalikan semua ABK aktif.
    ABK yang sedang di trip 'berlayar' → blocked=true
    ABK yang sedang di trip 'persiapan' → conflict={trip_id, kapal_nama}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.master.models import ABK
        trip_id = request.query_params.get('trip_id')

        # Semua TripABK di trip aktif (persiapan / berlayar)
        active_abk = TripABK.objects.filter(
            trip__status__in=['persiapan', 'berlayar']
        ).select_related('trip__kapal').exclude(
            trip_id=trip_id  # exclude trip saat ini
        )

        # Map abk_id → TripABK
        conflict_map = {}
        blocked_map = {}
        for ta in active_abk:
            if ta.trip.status == 'berlayar':
                blocked_map[ta.abk_id] = ta
            else:  # persiapan
                conflict_map[ta.abk_id] = ta

        from apps.master.models import ABK as ABKModel
        abk_list = ABKModel.objects.filter(aktif=True)
        result = []
        for abk in abk_list:
            entry = {'id': abk.id, 'nama': abk.nama, 'no_hp': abk.no_hp or ''}
            if abk.id in blocked_map:
                ta = blocked_map[abk.id]
                entry['blocked'] = True
                entry['conflict'] = {
                    'trip_id': ta.trip_id,
                    'kapal_nama': ta.trip.kapal.nama_kapal,
                    'status': 'berlayar',
                }
            elif abk.id in conflict_map:
                ta = conflict_map[abk.id]
                entry['blocked'] = False
                entry['conflict'] = {
                    'trip_id': ta.trip_id,
                    'kapal_nama': ta.trip.kapal.nama_kapal,
                    'status': 'persiapan',
                }
            else:
                entry['blocked'] = False
                entry['conflict'] = None
            result.append(entry)
        return Response(result)

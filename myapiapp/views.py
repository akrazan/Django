from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin

from myapiapp.serializers import UserSerializer, GroupSerializer
# from  myapiapp.permissions import IsOwnerOrStaff



class IsAdminOrReadOnly(permissions.BasePermission):
    """Админы могут всё, остальные — только читать."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['username', 'email', 'is_staff', 'is_active', 'groups']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined']


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['name']
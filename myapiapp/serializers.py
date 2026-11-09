# serializers.py
from django.contrib.auth.models import Group, User
from rest_framework import serializers

from shopapp.models import Product, Order


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'groups']
        read_only_fields = ['is_staff', 'is_active']  # лучше не менять через API без админки


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']
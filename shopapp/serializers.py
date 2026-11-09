# serializers.py
from rest_framework import serializers

from .models import Product, Order


class ProductSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'pk',
            'name',
            'description',
            'price',
            'discount',
            'created_by',           # ID пользователя
            'created_by_username',  # Имя пользователя
            'archived',
        ]


class OrderSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    products_names = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'pk',
            'delivery_address',
            'promo_code',
            'created_at',
            'user',           # ID пользователя
            'user_username',  # Имя пользователя
            'products',       # Список ID товаров
            'products_names',  # Список товаров
        ]
        read_only_fields = ['products_names']

    def get_products_names(self, obj):
        # Берем все связанные товары и собираем их имена в список.
        return list(obj.products.values_list('name', flat=True))
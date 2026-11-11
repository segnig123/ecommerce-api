from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Serialize order items using their historical product information."""

    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "unit_price",
            "quantity",
            "subtotal",
            "created_at",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Serialize an order with its associated items."""

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "status",
            "shipping_address",
            "shipping_phone",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    """Validate customer shipping information during checkout."""

    shipping_address = serializers.CharField()
    shipping_phone = serializers.CharField(max_length=20)
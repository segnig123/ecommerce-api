from decimal import Decimal

from rest_framework import serializers

from products.serializers import ProductSerializer
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    """Serialize cart items with product details and calculated subtotals."""

    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "quantity",
            "subtotal",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "product",
            "subtotal",
            "created_at",
            "updated_at",
        ]

    def get_subtotal(self, obj):
        """Calculate the subtotal using product price and quantity."""
        return obj.product.price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    """Serialize a shopping cart with its items and calculated total."""

    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "items",
            "total",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "items",
            "total",
            "created_at",
            "updated_at",
        ]

    def get_total(self, obj):
        """Calculate the total price of all items in the cart."""
        total = Decimal("0.00")

        for item in obj.items.all():
            total += item.product.price * item.quantity

        return total


class AddToCartSerializer(serializers.Serializer):
    """Validate product ID and quantity when adding a product to the cart."""

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    """Validate the new quantity when updating an existing cart item."""

    quantity = serializers.IntegerField(min_value=1)
from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """Serialize category data for API requests and responses."""

    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    """Serialize product data and validate price and category activation rules."""

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_price(self, value):
        """Ensure the product price is greater than zero."""

        if value <= 0:
            raise serializers.ValidationError(
            )

        return value

    def validate(self, attrs):
        """Prevent activating a product if its category is inactive."""

        category = attrs.get(
            "category",
            self.instance.category if self.instance else None
        )

        is_active = attrs.get(
            "is_active",
            self.instance.is_active if self.instance else True
        )

        if category and not category.is_active and is_active:
            raise serializers.ValidationError(
                "Cannot activate a product in an inactive category."
            )

        return attrs

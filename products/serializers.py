from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_price(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Product price must be greater than zero."
            )

        return value

    def validate(self, attrs):

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

from decimal import Decimal

from django.test import TestCase

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


# ==========================================
# CATEGORY SERIALIZER TESTS
# ==========================================

class CategorySerializerTests(TestCase):

    def test_valid_category_data(self):
        """Test that valid category data passes validation."""

        data = {
            "name": "Electronics",
            "slug": "electronics",
            "description": "Electronic products",
            "is_active": True
        }

        serializer = CategorySerializer(data=data)

        self.assertTrue(serializer.is_valid())

        self.assertEqual(
            serializer.validated_data["name"],
            "Electronics"
        )

    def test_invalid_category_data(self):
        """Test that missing required fields are rejected."""

        data = {
            "description": "Electronic products"
        }

        serializer = CategorySerializer(data=data)

        self.assertFalse(serializer.is_valid())

        self.assertIn("name", serializer.errors)
        self.assertIn("slug", serializer.errors)

    def test_category_read_only_fields(self):
        """Test that ID and timestamps are read-only."""

        data = {
            "id": 100,
            "name": "Electronics",
            "slug": "electronics",
            "created_at": "2026-01-01T10:00:00Z",
            "updated_at": "2026-01-01T10:00:00Z"
        }

        serializer = CategorySerializer(data=data)

        self.assertTrue(serializer.is_valid())

        self.assertNotIn("id", serializer.validated_data)
        self.assertNotIn("created_at", serializer.validated_data)
        self.assertNotIn("updated_at", serializer.validated_data)


# ==========================================
# PRODUCT SERIALIZER TESTS
# ==========================================

class ProductSerializerTests(TestCase):

    def setUp(self):
        """Create a category for product serializer tests."""

        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic products",
            is_active=True
        )

        self.valid_data = {
            "category": self.category.id,
            "name": "Gaming Laptop",
            "slug": "gaming-laptop",
            "description": "High-performance gaming laptop",
            "sku": "LAP-001",
            "price": "1500.00",
            "stock_quantity": 10,
            "is_active": True
        }

    def test_valid_product_data(self):
        """Test that valid product data passes validation."""

        serializer = ProductSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertEqual(
            serializer.validated_data["name"],
            "Gaming Laptop"
        )

        self.assertEqual(
            serializer.validated_data["category"],
            self.category
        )

    def test_invalid_zero_price(self):
        """Test that a zero product price is rejected."""

        data = self.valid_data.copy()
        data["price"] = "0.00"

        serializer = ProductSerializer(data=data)

        self.assertFalse(serializer.is_valid())

        self.assertIn("price", serializer.errors)

    def test_invalid_negative_price(self):
        """Test that a negative product price is rejected."""

        data = self.valid_data.copy()
        data["price"] = "-100.00"

        serializer = ProductSerializer(data=data)

        self.assertFalse(serializer.is_valid())

        self.assertIn("price", serializer.errors)

    def test_invalid_category(self):
        """Test that a nonexistent category ID is rejected."""

        data = self.valid_data.copy()
        data["category"] = 999999

        serializer = ProductSerializer(data=data)

        self.assertFalse(serializer.is_valid())

        self.assertIn("category", serializer.errors)

    def test_active_product_with_inactive_category(self):
        """Test that an active product cannot belong to an inactive category."""

        self.category.is_active = False
        self.category.save()

        serializer = ProductSerializer(data=self.valid_data)

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "non_field_errors",
            serializer.errors
        )

    def test_inactive_product_with_inactive_category(self):
        """Test that an inactive product can belong to an inactive category."""

        self.category.is_active = False
        self.category.save()

        data = self.valid_data.copy()
        data["is_active"] = False

        serializer = ProductSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_product_read_only_fields(self):
        """Test that ID and timestamps are read-only."""

        data = self.valid_data.copy()

        data.update({
            "id": 100,
            "created_at": "2026-01-01T10:00:00Z",
            "updated_at": "2026-01-01T10:00:00Z"
        })

        serializer = ProductSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertNotIn("id", serializer.validated_data)
        self.assertNotIn("created_at", serializer.validated_data)
        self.assertNotIn("updated_at", serializer.validated_data)

    def test_partial_update(self):
        """Test that partial updates preserve existing product fields."""

        product = Product.objects.create(
            **{
                **self.valid_data,
                "category": self.category
            }
        )

        updated_data = {
            "price": "1800.00"
        }

        serializer = ProductSerializer(
            instance=product,
            data=updated_data,
            partial=True
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_product = serializer.save()

        self.assertEqual(updated_product.price, Decimal("1800.00"))
        self.assertEqual(updated_product.name, "Gaming Laptop")
        self.assertEqual(updated_product.category, self.category)
        self.assertTrue(updated_product.is_active)

    def test_validated_data(self):
        """Test that serializer produces correctly validated data."""

        serializer = ProductSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        validated_data = serializer.validated_data

        self.assertEqual(validated_data["slug"], "gaming-laptop")
        self.assertEqual(validated_data["sku"], "LAP-001")
        self.assertEqual(validated_data["price"], Decimal("1500.00"))
        self.assertEqual(validated_data["stock_quantity"], 10)
        self.assertTrue(validated_data["is_active"])

    def test_inactive_category_rejects_partial_activation(self):
        """Test that an inactive category cannot have its product activated."""

        self.category.is_active = False
        self.category.save()

        product = Product.objects.create(
            **{
                **self.valid_data,
                "category": self.category,
                "is_active": False
            }
        )

        serializer = ProductSerializer(
            instance=product,
            data={"is_active": True},
            partial=True
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "non_field_errors",
            serializer.errors
        )
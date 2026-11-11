from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from products.models import Category, Product
from .models import Order, OrderItem
from .serializers import (
    OrderItemSerializer,
    OrderSerializer,
    CheckoutSerializer,
    OrderStatusUpdateSerializer,
)

User = get_user_model()


class OrderItemSerializerTest(TestCase):
    """Test serialization of order items."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpassword123",
        )

        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Laptop",
            slug="laptop",
            description="Test laptop",
            sku="LAPTOP-001",
            price=Decimal("1500.00"),
            stock_quantity=10,
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address="123 Test Street",
            shipping_phone="+251912345678",
            total_amount=Decimal("3000.00"),
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name="Laptop",
            unit_price=Decimal("1500.00"),
            quantity=2,
        )

    def test_order_item_serialization(self):
        """Test that order item data is serialized correctly."""

        serializer = OrderItemSerializer(self.order_item)

        self.assertEqual(serializer.data["product"], self.product.id)
        self.assertEqual(serializer.data["product_name"], "Laptop")
        self.assertEqual(serializer.data["unit_price"], "1500.00")
        self.assertEqual(serializer.data["quantity"], 2)
        self.assertEqual(
            serializer.data["subtotal"],
            Decimal("3000.00"),
        )

    def test_order_item_fields_are_read_only(self):
        """Test that all order item fields are read-only."""

        serializer = OrderItemSerializer()

        for field in serializer.fields.values():
            self.assertTrue(field.read_only)


class OrderSerializerTest(TestCase):
    """Test serialization of orders."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpassword123",
        )

        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Laptop",
            slug="laptop",
            description="Test laptop",
            sku="LAPTOP-001",
            price=Decimal("1500.00"),
            stock_quantity=10,
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address="123 Test Street",
            shipping_phone="+251912345678",
            total_amount=Decimal("3000.00"),
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name="Laptop",
            unit_price=Decimal("1500.00"),
            quantity=2,
        )

    def test_order_serialization(self):
        """Test that order data is serialized correctly."""

        serializer = OrderSerializer(self.order)

        self.assertEqual(serializer.data["user"], self.user.id)
        self.assertEqual(serializer.data["status"], Order.Status.PENDING)
        self.assertEqual(
            serializer.data["shipping_address"],
            "123 Test Street",
        )
        self.assertEqual(
            serializer.data["shipping_phone"],
            "+251912345678",
        )
        self.assertEqual(
            serializer.data["total_amount"],
            "3000.00",
        )

    def test_order_items_are_nested(self):
        """Test that order items are included in the serialized order."""

        serializer = OrderSerializer(self.order)

        self.assertEqual(len(serializer.data["items"]), 1)
        self.assertEqual(
            serializer.data["items"][0]["product_name"],
            "Laptop",
        )
        self.assertEqual(
            serializer.data["items"][0]["subtotal"],
            Decimal("3000.00"),
        )

    def test_order_fields_are_read_only(self):
        """Test that all order fields are read-only."""

        serializer = OrderSerializer()

        for field in serializer.fields.values():
            self.assertTrue(field.read_only)


class CheckoutSerializerTest(TestCase):
    """Test checkout shipping information validation."""

    def test_valid_checkout_data(self):
        """Test that valid checkout data passes validation."""

        data = {
            "shipping_address": "123 Test Street",
            "shipping_phone": "+251912345678",
        }

        serializer = CheckoutSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["shipping_address"],
            "123 Test Street",
        )
        self.assertEqual(
            serializer.validated_data["shipping_phone"],
            "+251912345678",
        )

    def test_shipping_address_is_required(self):
        """Test that shipping address cannot be omitted."""

        data = {
            "shipping_phone": "+251912345678",
        }

        serializer = CheckoutSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("shipping_address", serializer.errors)

    def test_shipping_phone_is_required(self):
        """Test that shipping phone cannot be omitted."""

        data = {
            "shipping_address": "123 Test Street",
        }

        serializer = CheckoutSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("shipping_phone", serializer.errors)

    def test_empty_shipping_address_is_invalid(self):
        """Test that an empty shipping address is rejected."""

        data = {
            "shipping_address": "",
            "shipping_phone": "+251912345678",
        }

        serializer = CheckoutSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("shipping_address", serializer.errors)

    def test_empty_shipping_phone_is_invalid(self):
        """Test that an empty shipping phone is rejected."""

        data = {
            "shipping_address": "123 Test Street",
            "shipping_phone": "",
        }

        serializer = CheckoutSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("shipping_phone", serializer.errors)

    def test_shipping_phone_max_length(self):
        """Test that shipping phone cannot exceed 20 characters."""

        data = {
            "shipping_address": "123 Test Street",
            "shipping_phone": "1" * 21,
        }

        serializer = CheckoutSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("shipping_phone", serializer.errors)


class OrderStatusUpdateSerializerTest(TestCase):
    """Test order status update validation."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpassword123",
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address="123 Test Street",
            shipping_phone="+251912345678",
            total_amount=Decimal("3000.00"),
        )

    def test_valid_status_update(self):
        """Test that a valid order status passes validation."""

        serializer = OrderStatusUpdateSerializer(
            instance=self.order,
            data={"status": Order.Status.SHIPPED},
        )

        self.assertTrue(serializer.is_valid())

        updated_order = serializer.save()

        self.assertEqual(
            updated_order.status,
            Order.Status.SHIPPED,
        )

    def test_invalid_status_update(self):
        """Test that an invalid order status is rejected."""

        serializer = OrderStatusUpdateSerializer(
            instance=self.order,
            data={"status": "invalid_status"},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_status_is_required(self):
        """Test that status cannot be omitted."""

        serializer = OrderStatusUpdateSerializer(
            instance=self.order,
            data={},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)
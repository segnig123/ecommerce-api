from decimal import Decimal
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from products.models import Category, Product
from orders.models import Order, OrderItem


User = get_user_model()


class OrderModelTest(TestCase):
    """Test the Order model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpassword123"
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address="Addis Ababa, Ethiopia",
            shipping_phone="+251911234567"
        )

    def test_order_creation(self):
        """Test that an order is created successfully."""

        self.assertEqual(self.order.user, self.user)
        self.assertEqual(
            self.order.shipping_address,
            "Addis Ababa, Ethiopia"
        )
        self.assertEqual(
            self.order.shipping_phone,
            "+251911234567"
        )
        self.assertEqual(self.order.total_amount, Decimal("0.00"))

    def test_order_number_is_valid_uuid(self):
        """Test that the order number is automatically generated as a UUID."""

        self.assertIsInstance(self.order.order_number, UUID)

    def test_order_number_is_unique(self):
        """Test that each order receives a unique order number."""

        another_order = Order.objects.create(
            user=self.user,
            shipping_address="Jimma, Ethiopia",
            shipping_phone="+251922345678"
        )

        self.assertNotEqual(
            self.order.order_number,
            another_order.order_number
        )

    def test_default_order_status(self):
        """Test that a new order has pending status."""

        self.assertEqual(
            self.order.status,
            Order.Status.PENDING
        )

    def test_order_string_representation(self):
        """Test the string representation of an order."""

        expected = f"Order {self.order.order_number} - {self.user}"

        self.assertEqual(str(self.order), expected)

    def test_order_status_choices(self):
        """Test that all expected order statuses are available."""

        expected_statuses = [
            "pending",
            "confirmed",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
        ]

        actual_statuses = [
            value for value, label in Order.Status.choices
        ]

        self.assertEqual(actual_statuses, expected_statuses)


class OrderItemModelTest(TestCase):
    """Test the OrderItem model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpassword123"
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address="Addis Ababa, Ethiopia",
            shipping_phone="+251911234567"
        )

        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Laptop",
            slug="laptop",
            description="Test laptop",
            sku="LAPTOP-001",
            price=Decimal("1500.00"),
            stock_quantity=10
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            unit_price=Decimal("1500.00"),
            quantity=2
        )

    def test_order_item_creation(self):
        """Test that an order item is created successfully."""

        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.product, self.product)
        self.assertEqual(self.order_item.product_name, "Laptop")
        self.assertEqual(self.order_item.unit_price, Decimal("1500.00"))
        self.assertEqual(self.order_item.quantity, 2)

    def test_order_item_subtotal(self):
        """Test that the subtotal is calculated correctly."""

        self.assertEqual(
            self.order_item.subtotal,
            Decimal("3000.00")
        )

    def test_order_item_string_representation(self):
        """Test the string representation of an order item."""

        expected = "Laptop x 2"

        self.assertEqual(str(self.order_item), expected)

    def test_order_item_product_can_be_null(self):
        """Test that an order item preserves its data if its product is deleted."""

        self.product.delete()

        self.order_item.refresh_from_db()

        self.assertIsNone(self.order_item.product)
        self.assertEqual(self.order_item.product_name, "Laptop")
        self.assertEqual(self.order_item.unit_price, Decimal("1500.00"))

    def test_order_item_quantity_must_be_positive(self):
        """Test that zero quantity violates the database constraint."""

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrderItem.objects.create(
                    order=self.order,
                    product=self.product,
                    product_name="Laptop",
                    unit_price=Decimal("1500.00"),
                    quantity=0
                )

    def test_order_item_price_must_be_positive(self):
        """Test that zero unit price violates the database constraint."""

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrderItem.objects.create(
                    order=self.order,
                    product=self.product,
                    product_name="Laptop",
                    unit_price=Decimal("0.00"),
                    quantity=1
                )
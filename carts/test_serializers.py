from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from products.models import Category, Product

from .models import Cart, CartItem
from .serializers import (
    CartItemSerializer,
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)


User = get_user_model()


class CartItemSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="segni",
            email="segni@example.com",
            password="testpassword123"
        )

        self.cart = Cart.objects.create(user=self.user)

        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Laptop",
            slug="laptop",
            sku="LAP-001",
            price=Decimal("1200.00"),
            stock_quantity=10
        )

        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

    def test_cart_item_serialization(self):
        serializer = CartItemSerializer(self.cart_item)

        self.assertEqual(serializer.data["id"], self.cart_item.id)
        self.assertEqual(serializer.data["quantity"], 2)
        self.assertEqual(serializer.data["product"]["name"], "Laptop")

    def test_cart_item_subtotal(self):
        serializer = CartItemSerializer(self.cart_item)

        self.assertEqual(
            Decimal(serializer.data["subtotal"]),
            Decimal("2400.00")
        )

    def test_product_is_read_only(self):
        serializer = CartItemSerializer()

        self.assertTrue(serializer.fields["product"].read_only)


class CartSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="segni",
            email="segni@example.com",
            password="testpassword123"
        )

        self.cart = Cart.objects.create(user=self.user)

        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )

        self.product1 = Product.objects.create(
            category=self.category,
            name="Laptop",
            slug="laptop",
            sku="LAP-001",
            price=Decimal("1200.00"),
            stock_quantity=10
        )

        self.product2 = Product.objects.create(
            category=self.category,
            name="Mouse",
            slug="mouse",
            sku="MOU-001",
            price=Decimal("25.00"),
            stock_quantity=20
        )

        CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            quantity=2
        )

        CartItem.objects.create(
            cart=self.cart,
            product=self.product2,
            quantity=1
        )

    def test_cart_serialization(self):
        serializer = CartSerializer(self.cart)

        self.assertEqual(serializer.data["id"], self.cart.id)
        self.assertEqual(serializer.data["user"], self.user.id)
        self.assertEqual(len(serializer.data["items"]), 2)

    def test_cart_total_calculation(self):
        serializer = CartSerializer(self.cart)

        self.assertEqual(
            Decimal(serializer.data["total"]),
            Decimal("2425.00")
        )

    def test_cart_items_are_read_only(self):
        serializer = CartSerializer()

        self.assertTrue(serializer.fields["items"].read_only)

    def test_cart_total_is_read_only(self):
        serializer = CartSerializer()

        self.assertTrue(serializer.fields["total"].read_only)


class AddToCartSerializerTest(TestCase):

    def test_valid_data(self):
        data = {
            "product_id": 1,
            "quantity": 2
        }

        serializer = AddToCartSerializer(data=data)

        self.assertTrue(serializer.is_valid())

        self.assertEqual(serializer.validated_data["product_id"], 1)
        self.assertEqual(serializer.validated_data["quantity"], 2)

    def test_missing_product_id(self):
        data = {
            "quantity": 2
        }

        serializer = AddToCartSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("product_id", serializer.errors)

    def test_missing_quantity(self):
        data = {
            "product_id": 1
        }

        serializer = AddToCartSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_invalid_product_id(self):
        data = {
            "product_id": "invalid",
            "quantity": 2
        }

        serializer = AddToCartSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("product_id", serializer.errors)

    def test_zero_quantity(self):
        data = {
            "product_id": 1,
            "quantity": 0
        }

        serializer = AddToCartSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_negative_quantity(self):
        data = {
            "product_id": 1,
            "quantity": -2
        }

        serializer = AddToCartSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)


class UpdateCartItemSerializerTest(TestCase):

    def test_valid_quantity(self):
        data = {"quantity": 5}

        serializer = UpdateCartItemSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["quantity"], 5)

    def test_missing_quantity(self):
        data = {}

        serializer = UpdateCartItemSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_zero_quantity(self):
        data = {"quantity": 0}

        serializer = UpdateCartItemSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_negative_quantity(self):
        data = {"quantity": -3}

        serializer = UpdateCartItemSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_invalid_quantity_type(self):
        data = {"quantity": "invalid"}

        serializer = UpdateCartItemSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)
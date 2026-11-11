from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from accounts.models import User
from products.models import Category, Product

from .models import Cart, CartItem


User = get_user_model()


class CartModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="segni",
            email="segni@example.com",
            password="testpassword123"
        )

    def test_create_cart(self):
        cart = Cart.objects.create(user=self.user)

        self.assertEqual(cart.user, self.user)
        self.assertIsNotNone(cart.created_at)
        self.assertIsNotNone(cart.updated_at)

    def test_cart_string_representation(self):
        cart = Cart.objects.create(user=self.user)

        self.assertEqual(str(cart), f"Cart - {self.user}")

    def test_one_cart_per_user(self):
        Cart.objects.create(user=self.user)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Cart.objects.create(user=self.user)

    def test_cart_user_relationship(self):
        cart = Cart.objects.create(user=self.user)

        self.assertEqual(cart.user, self.user)
        self.assertEqual(self.user.cart, cart)


class CartItemModelTest(TestCase):

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
            description="A test laptop",
            sku="LAP-001",
            price=Decimal("1200.00"),
            stock_quantity=10
        )

    def test_create_cart_item(self):
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        self.assertEqual(cart_item.cart, self.cart)
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 2)
        self.assertIsNotNone(cart_item.created_at)
        self.assertIsNotNone(cart_item.updated_at)

    def test_cart_item_string_representation(self):
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        self.assertEqual(str(cart_item), "Laptop x 2")

    def test_unique_product_per_cart(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CartItem.objects.create(
                    cart=self.cart,
                    product=self.product,
                    quantity=3
                )

    def test_cart_item_quantity_must_be_positive(self):
        for quantity in [0, -1]:
            with self.subTest(quantity=quantity):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        CartItem.objects.create(
                            cart=self.cart,
                            product=self.product,
                            quantity=quantity
                        )

    def test_cart_can_have_multiple_products(self):
        second_product = Product.objects.create(
            category=self.category,
            name="Mouse",
            slug="mouse",
            sku="MOU-001",
            price=Decimal("25.00"),
            stock_quantity=20
        )

        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        CartItem.objects.create(
            cart=self.cart,
            product=second_product,
            quantity=1
        )

        self.assertEqual(self.cart.items.count(), 2)

    def test_product_can_exist_in_different_carts(self):
        another_user = User.objects.create_user(
            username="anotheruser",
            email="another@example.com",
            password="testpassword123"
        )

        another_cart = Cart.objects.create(user=another_user)

        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        CartItem.objects.create(
            cart=another_cart,
            product=self.product,
            quantity=3
        )

        self.assertEqual(self.product.cart_items.count(), 2)

    def test_delete_cart_deletes_cart_items(self):
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        self.cart.delete()

        self.assertFalse(
            CartItem.objects.filter(id=cart_item.id).exists()
        )

    def test_delete_product_deletes_cart_items(self):
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        self.product.delete()

        self.assertFalse(
            CartItem.objects.filter(id=cart_item.id).exists()
        )
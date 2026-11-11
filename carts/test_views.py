from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from products.models import Category, Product
from .models import Cart, CartItem


User = get_user_model()


class CartDetailViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="segni",
            email="segni@example.com",
            password="testpassword123"
        )

        self.client.force_authenticate(user=self.user)

        self.url = "/api/cart/"

    def test_get_cart_creates_cart_if_not_exists(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_get_existing_cart(self):
        cart = Cart.objects.create(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], cart.id)

    def test_get_cart_with_items(self):
        cart = Cart.objects.create(user=self.user)

        category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )

        product = Product.objects.create(
            category=category,
            name="Laptop",
            slug="laptop",
            sku="LAP-001",
            price=Decimal("1200.00"),
            stock_quantity=10
        )

        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(
            Decimal(str(response.data["total"])),
            Decimal("2400.00")
        )


class AddToCartViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="segni",
            email="segni@example.com",
            password="testpassword123"
        )

        self.client.force_authenticate(user=self.user)

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

        self.url = "/api/cart/items/"

    def test_add_product_to_cart(self):
        response = self.client.post(
            self.url,
            {
                "product_id": self.product.id,
                "quantity": 2
            }
        )

        self.assertEqual(response.status_code, 200)

        cart_item = CartItem.objects.get(
            cart__user=self.user,
            product=self.product
        )

        self.assertEqual(cart_item.quantity, 2)

    def test_add_existing_product_increases_quantity(self):
        self.client.post(
            self.url,
            {
                "product_id": self.product.id,
                "quantity": 2
            }
        )

        response = self.client.post(
            self.url,
            {
                "product_id": self.product.id,
                "quantity": 3
            }
        )

        self.assertEqual(response.status_code, 200)

        cart_item = CartItem.objects.get(
            cart__user=self.user,
            product=self.product
        )

        self.assertEqual(cart_item.quantity, 5)

    def test_add_product_exceeding_stock(self):
        response = self.client.post(
            self.url,
            {
                "product_id": self.product.id,
                "quantity": 11
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

        self.assertFalse(
            CartItem.objects.filter(
                cart__user=self.user,
                product=self.product
            ).exists()
        )

    def test_add_existing_product_exceeding_stock(self):
        self.client.post(
            self.url,
            {
                "product_id": self.product.id,
                "quantity": 7
            }
        )

        response = self.client.post(
            self.url,
            {
                "product_id": self.product.id,
                "quantity": 5
            }
        )

        self.assertEqual(response.status_code, 400)

        cart_item = CartItem.objects.get(
            cart__user=self.user,
            product=self.product
        )

        self.assertEqual(cart_item.quantity, 7)

    def test_add_inactive_product(self):
        self.product.is_active = False
        self.product.save()

        response = self.client.post(
            self.url,
            {
                "product_id": self.product.id,
                "quantity": 1
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_add_nonexistent_product(self):
        response = self.client.post(
            self.url,
            {
                "product_id": 9999,
                "quantity": 1
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_add_product_with_invalid_quantity(self):
        response = self.client.post(
            self.url,
            {
                "product_id": self.product.id,
                "quantity": 0
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_add_product_without_required_fields(self):
        response = self.client.post(
            self.url,
            {}
        )

        self.assertEqual(response.status_code, 400)


class CartItemDetailViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="segni",
            email="segni@example.com",
            password="testpassword123"
        )

        self.client.force_authenticate(user=self.user)

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

        self.cart = Cart.objects.create(user=self.user)

        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        self.url = f"/api/cart/items/{self.cart_item.id}/"

    def test_update_cart_item_quantity(self):
        response = self.client.patch(
            self.url,
            {"quantity": 5},
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.cart_item.refresh_from_db()

        self.assertEqual(self.cart_item.quantity, 5)

    def test_update_quantity_exceeding_stock(self):
        response = self.client.patch(
            self.url,
            {"quantity": 11},
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        self.cart_item.refresh_from_db()

        self.assertEqual(self.cart_item.quantity, 2)

    def test_update_with_invalid_quantity(self):
        response = self.client.patch(
            self.url,
            {"quantity": 0},
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_update_nonexistent_cart_item(self):
        response = self.client.patch(
            "/api/cart/items/9999/",
            {"quantity": 3},
            format="json"
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_update_another_users_cart_item(self):
        another_user = User.objects.create_user(
            username="anotheruser",
            email="another@example.com",
            password="testpassword123"
        )

        self.client.force_authenticate(user=another_user)

        response = self.client.patch(
            self.url,
            {"quantity": 5},
            format="json"
        )

        self.assertEqual(response.status_code, 404)

    def test_delete_cart_item(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            CartItem.objects.filter(id=self.cart_item.id).exists()
        )

    def test_user_cannot_delete_another_users_cart_item(self):
        another_user = User.objects.create_user(
            username="anotheruser",
            email="another@example.com",
            password="testpassword123"
        )

        self.client.force_authenticate(user=another_user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            CartItem.objects.filter(id=self.cart_item.id).exists()
        )


class ClearCartViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="segni",
            email="segni@example.com",
            password="testpassword123"
        )

        self.client.force_authenticate(user=self.user)

        self.url = "/api/cart/"

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

    def test_clear_cart(self):
        cart = Cart.objects.create(user=self.user)

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )

        response = self.client.delete(
            "/api/cart/clear/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(cart.items.count(), 0)

    def test_clear_cart_without_existing_cart(self):
        response = self.client.delete(
            "/api/cart/clear/"
        )

        self.assertEqual(response.status_code, 204)

    def test_clear_cart_does_not_delete_other_users_items(self):
        another_user = User.objects.create_user(
            username="anotheruser",
            email="another@example.com",
            password="testpassword123"
        )

        another_cart = Cart.objects.create(user=another_user)

        another_item = CartItem.objects.create(
            cart=another_cart,
            product=self.product,
            quantity=2
        )

        Cart.objects.create(user=self.user)

        response = self.client.delete(
            "/api/cart/clear/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            CartItem.objects.filter(id=another_item.id).exists()
        )
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Category, Product
from carts.models import Cart, CartItem
from .models import Order, OrderItem

User = get_user_model()


class OrderAPITestBase(APITestCase):
    """Provide shared setup and helper methods for order API tests."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpassword123",
        )

        self.other_customer = User.objects.create_user(
            username="other_customer",
            email="other@example.com",
            password="testpassword123",
        )

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpassword123",
            is_staff=True,
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

    def create_order(
        self,
        user=None,
        status_value=Order.Status.PENDING,
        total_amount=Decimal("1500.00"),
    ):
        """Create an order for testing."""

        return Order.objects.create(
            user=user or self.customer,
            status=status_value,
            shipping_address="123 Test Street",
            shipping_phone="+251912345678",
            total_amount=total_amount,
        )

    def create_order_item(self, order, quantity=1):
        """Create an order item for a given order."""

        return OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=quantity,
        )

    def get_list_data(self, response):
        """Return list data whether pagination is enabled or disabled."""

        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]

        return response.data


class CheckoutViewTest(OrderAPITestBase):
    """Test checkout API behavior."""

    def setUp(self):
        super().setUp()

        self.url = reverse("orders:checkout")

        self.cart = Cart.objects.create(user=self.customer)

        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
        )

        self.client.force_authenticate(user=self.customer)

        self.checkout_data = {
            "shipping_address": "123 Test Street",
            "shipping_phone": "+251912345678",
        }

    def test_successful_checkout(self):
        """Test that checkout creates an order successfully."""

        response = self.client.post(
            self.url,
            self.checkout_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        order = Order.objects.get()

        self.assertEqual(order.user, self.customer)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.total_amount, Decimal("3000.00"))
        self.assertEqual(
            order.shipping_address,
            "123 Test Street",
        )

        order_item = OrderItem.objects.get()

        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.product_name, "Laptop")
        self.assertEqual(order_item.unit_price, Decimal("1500.00"))
        self.assertEqual(order_item.quantity, 2)

        self.product.refresh_from_db()

        self.assertEqual(self.product.stock_quantity, 8)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_checkout_requires_authentication(self):
        """Test that unauthenticated users cannot checkout."""

        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.url,
            self.checkout_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_checkout_with_empty_cart(self):
        """Test that checkout fails when the cart is empty."""

        self.cart.items.all().delete()

        response = self.client.post(
            self.url,
            self.checkout_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_with_insufficient_stock(self):
        """Test that checkout fails when requested quantity exceeds stock."""

        self.cart_item.quantity = 20
        self.cart_item.save()

        response = self.client.post(
            self.url,
            self.checkout_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(Order.objects.count(), 0)

        self.product.refresh_from_db()

        self.assertEqual(self.product.stock_quantity, 10)

        self.assertEqual(CartItem.objects.count(), 1)

    def test_checkout_with_inactive_product(self):
        """Test that inactive products cannot be purchased."""

        self.product.is_active = False
        self.product.save()

        response = self.client.post(
            self.url,
            self.checkout_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_requires_shipping_address(self):
        """Test that checkout requires a shipping address."""

        data = {
            "shipping_phone": "+251912345678",
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_requires_shipping_phone(self):
        """Test that checkout requires a shipping phone."""

        data = {
            "shipping_address": "123 Test Street",
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(Order.objects.count(), 0)


class OrderListViewTest(OrderAPITestBase):
    """Test customer order history API."""

    def setUp(self):
        super().setUp()

        self.url = reverse("orders:order-list")

        self.order1 = self.create_order(
            total_amount=Decimal("1500.00"),
        )

        self.order2 = self.create_order(
            status_value=Order.Status.SHIPPED,
            total_amount=Decimal("3000.00"),
        )

        self.other_order = self.create_order(
            user=self.other_customer,
            total_amount=Decimal("5000.00"),
        )

        self.client.force_authenticate(user=self.customer)

    def test_list_customer_orders(self):
        """Test that customers only see their own orders."""

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        orders = self.get_list_data(response)

        self.assertEqual(len(orders), 2)

        returned_ids = [order["id"] for order in orders]

        self.assertIn(self.order1.id, returned_ids)
        self.assertIn(self.order2.id, returned_ids)
        self.assertNotIn(self.other_order.id, returned_ids)

    def test_order_list_requires_authentication(self):
        """Test that unauthenticated users cannot view order history."""

        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_filter_orders_by_status(self):
        """Test filtering orders by status."""

        response = self.client.get(
            self.url,
            {"status": Order.Status.SHIPPED},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        orders = self.get_list_data(response)

        self.assertEqual(len(orders), 1)
        self.assertEqual(
            orders[0]["id"],
            self.order2.id,
        )

    def test_search_orders_by_order_number(self):
        """Test searching orders using their UUID order number."""

        response = self.client.get(
            self.url,
            {"search": str(self.order1.order_number)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        orders = self.get_list_data(response)

        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["id"], self.order1.id)

    def test_ordering_orders_by_total_amount(self):
        """Test ordering customer orders by total amount."""

        response = self.client.get(
            self.url,
            {"ordering": "total_amount"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        orders = self.get_list_data(response)

        amounts = [
            Decimal(str(order["total_amount"]))
            for order in orders
        ]

        self.assertEqual(amounts, sorted(amounts))


class OrderDetailViewTest(OrderAPITestBase):
    """Test retrieving individual order details."""

    def setUp(self):
        super().setUp()

        self.order = self.create_order()

        self.create_order_item(self.order, quantity=2)

        self.url = reverse(
            "orders:order-detail",
            kwargs={"pk": self.order.pk},
        )

        self.client.force_authenticate(user=self.customer)

    def test_retrieve_order_details(self):
        """Test retrieving an order belonging to the customer."""

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["id"], self.order.id)
        self.assertEqual(
            response.data["order_number"],
            str(self.order.order_number),
        )

        self.assertEqual(len(response.data["items"]), 1)

        self.assertEqual(
            response.data["items"][0]["product_name"],
            "Laptop",
        )

    def test_order_detail_requires_authentication(self):
        """Test that unauthenticated users cannot retrieve orders."""

        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_cannot_retrieve_another_customers_order(self):
        """Test that customers cannot access another customer's order."""

        other_order = self.create_order(
            user=self.other_customer,
        )

        url = reverse(
            "orders:order-detail",
            kwargs={"pk": other_order.pk},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_retrieve_nonexistent_order(self):
        """Test retrieving an order that does not exist."""

        url = reverse(
            "orders:order-detail",
            kwargs={"pk": 99999},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class OrderStatusUpdateViewTest(OrderAPITestBase):
    """Test administrator order status update API."""

    def setUp(self):
        super().setUp()

        self.order = self.create_order()

        self.url = reverse(
            "orders:order-status-update",
            kwargs={"pk": self.order.pk},
        )

        self.valid_data = {
            "status": Order.Status.SHIPPED,
        }

    def test_admin_can_update_order_status(self):
        """Test that administrators can update order status."""

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            self.url,
            self.valid_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            Order.Status.SHIPPED,
        )

    def test_customer_cannot_update_order_status(self):
        """Test that ordinary customers cannot update order status."""

        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            self.url,
            self.valid_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            Order.Status.PENDING,
        )

    def test_order_status_update_requires_authentication(self):
        """Test that unauthenticated users cannot update order status."""

        self.client.force_authenticate(user=None)

        response = self.client.patch(
            self.url,
            self.valid_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_admin_cannot_set_invalid_status(self):
        """Test that invalid order statuses are rejected."""

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            self.url,
            {"status": "invalid_status"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            Order.Status.PENDING,
        )

    def test_admin_must_provide_status(self):
        """Test that status is required when updating an order."""

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_admin_cannot_update_nonexistent_order(self):
        """Test updating an order that does not exist."""

        self.client.force_authenticate(user=self.admin)

        url = reverse(
            "orders:order-status-update",
            kwargs={"pk": 99999},
        )

        response = self.client.patch(
            url,
            self.valid_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
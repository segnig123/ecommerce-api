from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from orders.models import Order
from payments.models import Payment
from payments.serializers import PaymentSerializer



User = get_user_model()


class PaymentSerializerTest(TestCase):
    """Test PaymentSerializer validation and serialization."""

    def setUp(self):
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            username="customer1",
            email="customer1@example.com",
            password="testpassword123"
        )

        self.other_user = User.objects.create_user(
            username="customer2",
            email="customer2@example.com",
            password="testpassword123"
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address="123 Test Street",
            shipping_phone="1234567890",
            total_amount=Decimal("150.00")
        )

        self.request = self.factory.post("/api/payments/")
        self.request.user = self.user

    def test_valid_payment_creation(self):
        """Test successful payment creation."""

        serializer = PaymentSerializer(
            data={"order": self.order.pk},
            context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        payment = serializer.save()

        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.amount, Decimal("150.00"))
        self.assertEqual(payment.status, Payment.Status.PENDING)

    def test_amount_cannot_be_manipulated(self):
        """Test that clients cannot manipulate payment amounts."""

        serializer = PaymentSerializer(
            data={
                "order": self.order.pk,
                "amount": "1.00"
            },
            context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        payment = serializer.save()

        self.assertEqual(payment.amount, Decimal("150.00"))

    def test_status_cannot_be_manipulated(self):
        """Test that clients cannot set payment status."""

        serializer = PaymentSerializer(
            data={
                "order": self.order.pk,
                "status": Payment.Status.SUCCEEDED
            },
            context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        payment = serializer.save()

        self.assertEqual(payment.status, Payment.Status.PENDING)

    def test_user_cannot_pay_for_another_users_order(self):
        """Test that users cannot pay for orders they do not own."""

        other_order = Order.objects.create(
            user=self.other_user,
            shipping_address="456 Other Street",
            shipping_phone="0987654321",
            total_amount=Decimal("200.00")
        )

        serializer = PaymentSerializer(
            data={"order": other_order.pk},
            context={"request": self.request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("order", serializer.errors)

    def test_cancelled_order_payment_is_rejected(self):
        """Test that payment cannot be initiated for cancelled orders."""

        self.order.status = Order.Status.CANCELLED
        self.order.save()

        serializer = PaymentSerializer(
            data={"order": self.order.pk},
            context={"request": self.request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("order", serializer.errors)

    def test_already_paid_order_is_rejected(self):
        """Test that an already-paid order cannot be paid again."""

        Payment.objects.create(
            order=self.order,
            amount=self.order.total_amount,
            status=Payment.Status.SUCCEEDED
        )

        serializer = PaymentSerializer(
            data={"order": self.order.pk},
            context={"request": self.request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("order", serializer.errors)
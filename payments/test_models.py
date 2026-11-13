from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from orders.models import Order
from .models import StripeEvent
from payments.models import Payment
from django.contrib.auth import get_user_model


User = get_user_model()


class PaymentModelTest(TestCase):
    """Test the Payment model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address="123 Test Street",
            shipping_phone="1234567890",
            total_amount=Decimal("150.00")
        )

        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("150.00")
        )

    def test_payment_creation(self):
        """Test that a payment is created successfully."""

        self.assertEqual(self.payment.order, self.order)
        self.assertEqual(self.payment.amount, Decimal("150.00"))

    def test_default_status(self):
        """Test the default payment status."""

        self.assertEqual(
            self.payment.status,
            Payment.Status.PENDING
        )

    def test_default_currency(self):
        """Test the default payment currency."""

        self.assertEqual(self.payment.currency, "usd")

    def test_string_representation(self):
        """Test the payment string representation."""

        self.assertEqual(
            str(self.payment),
            f"Payment #{self.payment.pk} - pending"
        )

    def test_payment_amount_must_be_positive(self):
        """Test that the database rejects zero and negative amounts."""

        for amount in [Decimal("0.00"), Decimal("-10.00")]:
            with self.subTest(amount=amount):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        Payment.objects.create(
                            order=self.order,
                            amount=amount
                        )

    def test_order_can_have_multiple_payments(self):
        """Test that an order can have multiple payment attempts."""

        Payment.objects.create(
            order=self.order,
            amount=Decimal("150.00"),
            status=Payment.Status.FAILED
        )

        self.assertEqual(self.order.payments.count(), 2)

    def test_stripe_checkout_session_id_must_be_unique(self):
        """Test that Stripe Checkout Session IDs are unique."""

        Payment.objects.create(
            order=self.order,
            amount=Decimal("150.00"),
            stripe_checkout_session_id="cs_test_123"
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(
                    order=self.order,
                    amount=Decimal("150.00"),
                    stripe_checkout_session_id="cs_test_123"
                )

    def test_stripe_payment_intent_id_must_be_unique(self):
        """Test that Stripe Payment Intent IDs are unique."""

        Payment.objects.create(
            order=self.order,
            amount=Decimal("150.00"),
            stripe_payment_intent_id="pi_test_123"
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(
                    order=self.order,
                    amount=Decimal("150.00"),
                    stripe_payment_intent_id="pi_test_123"
                )

class StripeEventModelTest(TestCase):
    """Test Stripe webhook event model behavior."""

    def test_create_stripe_event(self):
        """Test that a Stripe event can be created."""

        event = StripeEvent.objects.create(
            event_id="evt_test_123",
            event_type="checkout.session.completed",
        )

        self.assertEqual(event.event_id, "evt_test_123")
        self.assertEqual(
            event.event_type,
            "checkout.session.completed",
        )
        self.assertIsNotNone(event.created_at)

    def test_stripe_event_string_representation(self):
        """Test the string representation of a Stripe event."""

        event = StripeEvent.objects.create(
            event_id="evt_test_456",
            event_type="payment_intent.payment_failed",
        )

        self.assertEqual(
            str(event),
            "payment_intent.payment_failed - evt_test_456",
        )

    def test_event_id_must_be_unique(self):
        """Test that duplicate Stripe event IDs are rejected."""

        StripeEvent.objects.create(
            event_id="evt_duplicate",
            event_type="checkout.session.completed",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StripeEvent.objects.create(
                    event_id="evt_duplicate",
                    event_type="checkout.session.expired",
                )
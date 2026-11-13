import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import stripe

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order
from .models import Payment, StripeEvent


User = get_user_model()


class PaymentCreateViewTest(APITestCase):
    """Test payment creation and Stripe Checkout Session generation."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="customer1",
            email="customer1@example.com",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="customer2",
            email="customer2@example.com",
            password="testpass123",
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address="123 Test Street",
            shipping_phone="1234567890",
            total_amount=Decimal("150.00"),
        )

        self.url = reverse("payments:payment-create")

        self.client.force_authenticate(user=self.user)

    @patch("payments.views.stripe.checkout.Session.create")
    def test_authenticated_user_can_create_payment(self, mock_create):
        """Test that an authenticated user can initiate payment."""

        mock_create.return_value = SimpleNamespace(
            id="cs_test_123",
            url="https://checkout.stripe.com/test",
        )

        response = self.client.post(
            self.url,
            {"order": self.order.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(order=self.order)

        self.assertEqual(payment.amount, Decimal("150.00"))
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(
            payment.stripe_checkout_session_id,
            "cs_test_123",
        )

        self.assertEqual(
            response.data["checkout_url"],
            "https://checkout.stripe.com/test",
        )

    def test_unauthenticated_user_cannot_create_payment(self):
        """Test that unauthenticated users cannot initiate payment."""

        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.url,
            {"order": self.order.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_pay_another_users_order(self):
        """Test that users cannot initiate payment for another user."""

        other_order = Order.objects.create(
            user=self.other_user,
            shipping_address="456 Other Street",
            shipping_phone="0987654321",
            total_amount=Decimal("100.00"),
        )

        response = self.client.post(
            self.url,
            {"order": other_order.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Payment.objects.filter(order=other_order).exists())

    def test_cannot_pay_cancelled_order(self):
        """Test that cancelled orders cannot be paid."""

        self.order.status = Order.Status.CANCELLED
        self.order.save()

        response = self.client.post(
            self.url,
            {"order": self.order.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_pay_already_paid_order(self):
        """Test that an order cannot be paid twice."""

        Payment.objects.create(
            order=self.order,
            amount=Decimal("150.00"),
            status=Payment.Status.SUCCEEDED,
        )

        response = self.client.post(
            self.url,
            {"order": self.order.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("payments.views.stripe.checkout.Session.create")
    def test_stripe_failure_marks_payment_as_failed(self, mock_create):
        """Test that Stripe errors mark payment as failed."""

        mock_create.side_effect = stripe.StripeError(
            message="Stripe connection failed."
        )

        response = self.client.post(
            self.url,
            {"order": self.order.id},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )

        payment = Payment.objects.get(order=self.order)

        self.assertEqual(payment.status, Payment.Status.FAILED)

    def test_missing_order_returns_error(self):
        """Test that payment creation requires an order."""

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_order_id_returns_error(self):
        """Test that an invalid order ID is rejected."""

        response = self.client.post(
            self.url,
            {"order": 99999},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StripeWebhookViewTest(APITestCase):
    """Test Stripe webhook event handling."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpass123",
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address="123 Test Street",
            shipping_phone="123456789",
            total_amount=Decimal("100.00"),
        )

        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("100.00"),
        )

        self.url = reverse("payments:stripe-webhook")

    def send_event(self, event_type, event_data, event_id="evt_test_123"):
        """Send a mocked Stripe webhook event."""

        event = {
            "id": event_id,
            "type": event_type,
            "data": {
                "object": event_data,
            },
        }

        with patch(
            "payments.views.stripe.Webhook.construct_event",
            return_value=event,
        ):
            return self.client.post(
                self.url,
                data=json.dumps({"test": "payload"}),
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test_signature",
            )

    def test_successful_checkout(self):
        """Test that successful checkout updates payment and order."""

        self.payment.stripe_checkout_session_id = "cs_test_123"
        self.payment.save()

        response = self.send_event(
            "checkout.session.completed",
            {
                "id": "cs_test_123",
                "payment_status": "paid",
                "payment_intent": "pi_test_123",
                "metadata": {
                    "payment_id": str(self.payment.id),
                },
            },
        )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCEEDED,
        )

        self.assertEqual(
            self.payment.stripe_payment_intent_id,
            "pi_test_123",
        )

        self.assertIsNotNone(self.payment.paid_at)

        self.assertEqual(
            self.order.status,
            Order.Status.CONFIRMED,
        )

    def test_expired_checkout(self):
        """Test that an expired checkout cancels the payment."""

        self.payment.stripe_checkout_session_id = "cs_test_123"
        self.payment.save()

        response = self.send_event(
            "checkout.session.expired",
            {
                "id": "cs_test_123",
            },
        )

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.payment.status,
            Payment.Status.CANCELLED,
        )

    def test_failed_payment(self):
        """Test that a failed payment updates its status and message."""

        response = self.send_event(
            "payment_intent.payment_failed",
            {
                "id": "pi_test_123",
                "metadata": {
                    "payment_id": str(self.payment.id),
                },
                "last_payment_error": {
                    "message": "Insufficient funds.",
                },
            },
        )

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.payment.status,
            Payment.Status.FAILED,
        )

        self.assertEqual(
            self.payment.failure_message,
            "Insufficient funds.",
        )

    def test_invalid_webhook_payload(self):
        """Test that invalid webhook payloads are rejected."""

        with patch(
            "payments.views.stripe.Webhook.construct_event",
            side_effect=ValueError("Invalid payload"),
        ):
            response = self.client.post(
                self.url,
                data="invalid payload",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test_signature",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_webhook_signature(self):
        """Test that invalid Stripe signatures are rejected."""

        with patch(
            "payments.views.stripe.Webhook.construct_event",
            side_effect=stripe.SignatureVerificationError(
                "Invalid signature",
                "test_signature",
            ),
        ):
            response = self.client.post(
                self.url,
                data=json.dumps({"test": "payload"}),
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="invalid_signature",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_webhook_does_not_require_authentication(self):
        """Test that Stripe can access the webhook without JWT."""

        response = self.send_event(
            "some.unknown.event",
            {},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_duplicate_webhook_event_is_not_processed_twice(self):
        """Test that duplicate Stripe events are ignored."""

        self.payment.stripe_checkout_session_id = "cs_test_123"
        self.payment.save()

        event_data = {
            "id": "cs_test_123",
            "payment_status": "paid",
            "payment_intent": "pi_test_123",
            "metadata": {
                "payment_id": str(self.payment.id),
            },
        }

        first_response = self.send_event(
            "checkout.session.completed",
            event_data,
        )

        second_response = self.send_event(
            "checkout.session.completed",
            event_data,
        )

        self.payment.refresh_from_db()

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            StripeEvent.objects.filter(event_id="evt_test_123").count(),
            1,
        )

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCEEDED,
        )
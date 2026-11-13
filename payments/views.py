import stripe

from decimal import Decimal

from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Payment,StripeEvent
from .serializers import PaymentSerializer

from django.db import transaction
from django.utils import timezone

from rest_framework.permissions import AllowAny

from orders.models import Order

class PaymentCreateView(APIView):
    """Create a payment and generate a Stripe Checkout Session."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a Stripe Checkout Session for an order."""

        serializer = PaymentSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)

        payment = serializer.save()

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            session = stripe.checkout.Session.create(
                mode="payment",

                payment_method_types=["card"],

                line_items=[
                    {
                        "price_data": {
                            "currency": payment.currency,
                            "product_data": {
                                "name": f"Order #{payment.order_id}",
                            },
                            "unit_amount": int(
                                payment.amount * Decimal("100")
                            ),
                        },
                        "quantity": 1,
                    }
                ],

                success_url=settings.STRIPE_SUCCESS_URL,
                cancel_url=settings.STRIPE_CANCEL_URL,

                metadata={
                    "payment_id": str(payment.id),
                    "order_id": str(payment.order_id),
                },

                payment_intent_data={
                    "metadata": {
                        "payment_id": str(payment.id),
                        "order_id": str(payment.order_id),
                    }
                }
            )

            payment.stripe_checkout_session_id = session.id
            payment.save(update_fields=[
                "stripe_checkout_session_id",
                "updated_at"
            ])

            return Response(
                {
                    "message": "Checkout session created successfully.",
                    "payment_id": payment.id,
                    "checkout_url": session.url,
                },
                status=status.HTTP_201_CREATED
            )

        except stripe.StripeError:
            payment.status = Payment.Status.FAILED
            payment.failure_message = (
                "Unable to create Stripe checkout session."
            )
            payment.save(update_fields=[
                "status",
                "failure_message",
                "updated_at"
            ])

            return Response(
                {"error": "Payment initialization failed."},
                status=status.HTTP_502_BAD_GATEWAY
            )


class StripeWebhookView(APIView):
    """Handle and verify incoming Stripe webhook events."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Verify Stripe events and process each event only once."""

        payload = request.body
        signature = request.headers.get("Stripe-Signature")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )

        except ValueError:
            return Response(
               {"error": "Invalid webhook payload."},
               status=status.HTTP_400_BAD_REQUEST,
        )

        except stripe.SignatureVerificationError:
            return Response(
                {"error": "Invalid webhook signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event_id = event["id"]
        event_type = event["type"]
        event_data = event["data"]["object"]

        with transaction.atomic():

            stripe_event, created = StripeEvent.objects.get_or_create(
                event_id=event_id,
                defaults={"event_type": event_type},
            )

            if not created:
               return Response(
                   {"message": "Event already processed."},
                   status=status.HTTP_200_OK,
                )

            if event_type == "checkout.session.completed":
               self.handle_checkout_completed(event_data)

            elif event_type == "checkout.session.expired":
               self.handle_checkout_expired(event_data)

            elif event_type == "payment_intent.payment_failed":
              self.handle_payment_failed(event_data)

        return Response(
             {"message": "Webhook received successfully."},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    @transaction.atomic
    def handle_checkout_completed(session):
        """Mark a payment as successful after checkout completion."""

        payment_id = session.get("metadata", {}).get("payment_id")

        if not payment_id or session.get("payment_status") != "paid":
            return

        payment = Payment.objects.select_for_update().filter(
            id=payment_id,
            stripe_checkout_session_id=session.get("id"),
        ).first()

        if not payment or payment.status != Payment.Status.PENDING:
            return

        payment.status = Payment.Status.SUCCEEDED
        payment.stripe_payment_intent_id = session.get(
            "payment_intent"
        )
        payment.paid_at = timezone.now()

        payment.save(update_fields=[
            "status",
            "stripe_payment_intent_id",
            "paid_at",
            "updated_at",
        ])

        Order.objects.filter(
            id=payment.order_id,
            status=Order.Status.PENDING,
        ).update(status=Order.Status.CONFIRMED)

    @staticmethod
    @transaction.atomic
    def handle_checkout_expired(session):
        """Mark a pending payment as cancelled when checkout expires."""

        payment = Payment.objects.select_for_update().filter(
            stripe_checkout_session_id=session.get("id"),
            status=Payment.Status.PENDING,
        ).first()

        if payment:
            payment.status = Payment.Status.CANCELLED
            payment.save(update_fields=["status", "updated_at"])

    @staticmethod
    @transaction.atomic
    def handle_payment_failed(payment_intent):
        """Record a failed payment attempt."""

        payment_id = payment_intent.get("metadata", {}).get("payment_id")

        if not payment_id:
            return

        payment = Payment.objects.select_for_update().filter(
            id=payment_id,
            status=Payment.Status.PENDING,
        ).first()

        if payment:
            payment.status = Payment.Status.FAILED
            payment.failure_message = (
                payment_intent.get("last_payment_error", {}).get(
                    "message",
                    "Payment failed.",
                )
            )
            payment.save(update_fields=[
                "status",
                "failure_message",
                "updated_at",
            ])
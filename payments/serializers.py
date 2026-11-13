from rest_framework import serializers

from .models import Payment
from orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    """Serialize payment information and validate payment creation."""

    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all()
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "amount",
            "currency",
            "status",
            "stripe_checkout_session_id",
            "stripe_payment_intent_id",
            "failure_message",
            "paid_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "amount",
            "currency",
            "status",
            "stripe_checkout_session_id",
            "stripe_payment_intent_id",
            "failure_message",
            "paid_at",
            "created_at",
            "updated_at",
        ]

    def validate_order(self, order):
        """Ensure the order belongs to the requesting user."""

        request = self.context.get("request")

        if request and order.user != request.user:
            raise serializers.ValidationError(
                "You cannot initiate payment for another user's order."
            )

        if order.status == Order.Status.CANCELLED:
            raise serializers.ValidationError(
                "Cannot initiate payment for a cancelled order."
            )

        if order.payments.filter(
            status=Payment.Status.SUCCEEDED
        ).exists():
            raise serializers.ValidationError(
                "This order has already been paid."
            )

        return order

    def create(self, validated_data):
        """Create a payment using the order's total amount."""

        order = validated_data["order"]

        return Payment.objects.create(
            order=order,
            amount=order.total_amount
        )
from django.urls import path

from .views import PaymentCreateView, StripeWebhookView


app_name = "payments"

urlpatterns = [
    path("", PaymentCreateView.as_view(), name="payment-create"),
    path(
        "webhook/",
        StripeWebhookView.as_view(),
        name="stripe-webhook",
    ),
]
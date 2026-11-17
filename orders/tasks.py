from celery import shared_task
from django.core.mail import send_mail

from .models import Order

import smtplib


@shared_task
def test_celery_task(message):
    return f"Background task completed: {message}"

@shared_task(
    autoretry_for=(smtplib.SMTPException, OSError, TimeoutError),
    retry_backoff=30,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def send_order_confirmation_email(order_id):
    order = (
        Order.objects
        .select_related("user")
        .prefetch_related("items")
        .get(id=order_id)
    )

    subject = f"Order Confirmation - {order.order_number}"

    items = "\n".join([
        f"{item.product_name} x {item.quantity} - ${item.subtotal}"
        for item in order.items.all()
    ])

    message = f"""
Hello {order.user.username},

Thank you for your purchase!

Your order has been successfully placed.

Order Number: {order.order_number}
Order Status: {order.status}

Items:
{items}

Total Amount: ${order.total_amount}

Shipping Address:
{order.shipping_address}

Thank you for shopping with us!
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=[order.user.email],
        fail_silently=False,
    )

    return f"Confirmation email sent for order {order.order_number}"
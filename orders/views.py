from django.db import transaction
from django.db.models import F
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView,ListAPIView, RetrieveAPIView

from carts.models import CartItem
from products.models import Product

from .models import Order, OrderItem
from .serializers import CheckoutSerializer, OrderSerializer, OrderStatusUpdateSerializer

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from drf_spectacular.utils import extend_schema_view

from .docs import (
    checkout_docs,
    order_list_docs,
    order_detail_docs,
    order_status_update_docs,
)

@checkout_docs
class CheckoutView(APIView):
    """Create an order from the authenticated user's shopping cart."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():

            # Retrieve and lock the user's cart items.
            cart_items = list(
                CartItem.objects
                .filter(cart__user=request.user)
                .select_related("product")
                .order_by("product_id")
            )

            if not cart_items:
                return Response(
                    {"detail": "Your shopping cart is empty."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Lock products to prevent concurrent stock deductions.
            product_ids = [item.product_id for item in cart_items]

            products = {
                product.id: product
                for product in Product.objects
                .select_for_update()
                .filter(id__in=product_ids)
            }

            total_amount = 0
            order_items = []

            # Validate products and calculate the total.
            for cart_item in cart_items:
                product = products.get(cart_item.product_id)

                if product is None or not product.is_active:
                    return Response(
                        {
                            "detail": (
                                f"{cart_item.product.name} is unavailable."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if product.stock_quantity < cart_item.quantity:
                    return Response(
                        {
                            "detail": (
                                f"Insufficient stock for {product.name}. "
                                f"Available: {product.stock_quantity}."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                subtotal = product.price * cart_item.quantity
                total_amount += subtotal

                order_items.append(
                    OrderItem(
                        product=product,
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=cart_item.quantity
                    )
                )

            # Create the order.
            order = Order.objects.create(
                user=request.user,
                shipping_address=serializer.validated_data[
                    "shipping_address"
                ],
                shipping_phone=serializer.validated_data[
                    "shipping_phone"
                ],
                total_amount=total_amount
            )

            # Associate order items with the new order.
            for item in order_items:
                item.order = order

            OrderItem.objects.bulk_create(order_items)

            # Deduct product stock.
            for item in order_items:
                Product.objects.filter(id=item.product_id).update(
                    stock_quantity=F("stock_quantity") - item.quantity
                )

            # Clear the shopping cart.
            CartItem.objects.filter(
                cart__user=request.user
            ).delete()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


@order_list_docs
class OrderListView(ListAPIView):
    """Return the authenticated user's order history."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = ["status"]

    search_fields = ["order_number"]

    ordering_fields = [
        "created_at",
        "updated_at",
        "total_amount",
        "status",
    ]

    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items")
        )

@order_detail_docs
class OrderDetailView(RetrieveAPIView):
    """Retrieve details of an order belonging to the authenticated user."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items")
        )

@order_status_update_docs
class OrderStatusUpdateView(UpdateAPIView):
    """Allow administrators to update an order's status."""

    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsAdminUser]
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)

from .serializers import (
    OrderSerializer,
    OrderStatusUpdateSerializer,
    CheckoutSerializer,
)


checkout_docs = extend_schema(
    summary="Checkout",
    description=(
        "Create an order using the authenticated user's shopping cart."
    ),
    request=CheckoutSerializer,
    responses={
        201: OrderSerializer,
        400: OpenApiResponse(
            description="Invalid checkout or insufficient stock."
        ),
    },
)


order_list_docs = extend_schema(
    summary="List customer orders",
    description=(
        "Retrieve the authenticated user's order history. "
        "Supports filtering, searching, and ordering."
    ),
    responses={
        200: OrderSerializer(many=True),
    },
)


order_detail_docs = extend_schema(
    summary="Retrieve order details",
    description=(
        "Retrieve details of an order belonging to the authenticated user."
    ),
    responses={
        200: OrderSerializer,
        404: OpenApiResponse(description="Order not found."),
    },
)


order_status_update_docs = extend_schema(
    summary="Update order status",
    description="Update an order's status. Admin access required.",
    request=OrderStatusUpdateSerializer,
    responses={
        200: OrderStatusUpdateSerializer,
        400: OpenApiResponse(description="Invalid order status."),
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="Order not found."),
    },
)
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)

from .serializers import (
    OrderSerializer,
    OrderStatusUpdateSerializer,
    CheckoutSerializer,
)


checkout_docs = extend_schema(
    summary="Checkout",
    description="Create an order using the authenticated user's shopping cart.",
    request=CheckoutSerializer,
    responses={
        201: OrderSerializer,
        400: OpenApiResponse(description="Invalid checkout or insufficient stock."),
    },
)


@extend_schema_view(
    get=extend_schema(
        summary="List customer orders",
        description="Retrieve the authenticated user's order history.",
        responses={200: OrderSerializer(many=True)},
    )
)
class OrderListDocs:
    pass


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve order details",
        description="Retrieve details of a specific customer order.",
        responses={200: OrderSerializer},
    )
)
class OrderDetailDocs:
    pass


order_status_update_docs = extend_schema(
    summary="Update order status",
    description="Update an order's status. Admin access required.",
    request=OrderStatusUpdateSerializer,
    responses={200: OrderStatusUpdateSerializer},
)
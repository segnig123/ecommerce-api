from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)


cart_detail_docs = extend_schema_view(
    get=extend_schema(
        summary="Retrieve shopping cart",
        description="Retrieve the authenticated user's shopping cart, including cart items and calculated totals.",
        responses={200: CartSerializer},
        tags=["Carts"],
    )
)


add_to_cart_docs = extend_schema_view(
    post=extend_schema(
        summary="Add product to cart",
        description=(
            "Add a product to the authenticated user's cart. "
            "If the product already exists, its quantity is increased. "
            "Available stock is validated."
        ),
        request=AddToCartSerializer,
        responses={
            200: CartSerializer,
            400: OpenApiResponse(description="Invalid data or insufficient stock."),
            404: OpenApiResponse(description="Product not found or inactive."),
        },
        tags=["Carts"],
    )
)


cart_item_detail_docs = extend_schema_view(
    patch=extend_schema(
        summary="Update cart item quantity",
        description="Update the quantity of an existing cart item belonging to the authenticated user.",
        request=UpdateCartItemSerializer,
        responses={
            200: CartSerializer,
            400: OpenApiResponse(description="Invalid quantity or insufficient stock."),
            404: OpenApiResponse(description="Cart item not found."),
        },
        tags=["Carts"],
    ),

    delete=extend_schema(
        summary="Remove cart item",
        description="Remove an individual item from the authenticated user's cart.",
        responses={
            200: CartSerializer,
            404: OpenApiResponse(description="Cart item not found."),
        },
        tags=["Carts"],
    )
)


clear_cart_docs = extend_schema_view(
    delete=extend_schema(
        summary="Clear shopping cart",
        description="Remove all items from the authenticated user's shopping cart.",
        responses={
            200: OpenApiResponse(description="Cart cleared successfully."),
            204: OpenApiResponse(description="Cart does not exist or is already empty."),
        },
        tags=["Carts"],
    )
)
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)

from .serializers import ProductSerializer, CategorySerializer


# =====================================================
# PRODUCT LIST AND CREATE DOCUMENTATION
# =====================================================

product_list_create_docs = extend_schema_view(
    get=extend_schema(
        summary="List products",
        description=(
            "Retrieve a paginated list of products. "
            "Supports filtering, searching, and ordering."
        ),
        parameters=[
            OpenApiParameter(
                name="category",
                description="Filter products by category ID.",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="price",
                description="Filter products by exact price.",
                required=False,
                type=float,
            ),
            OpenApiParameter(
                name="price__gte",
                description="Filter products with a minimum price.",
                required=False,
                type=float,
            ),
            OpenApiParameter(
                name="price__lte",
                description="Filter products with a maximum price.",
                required=False,
                type=float,
            ),
            OpenApiParameter(
                name="is_active",
                description="Filter products by active status.",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="search",
                description=(
                    "Search by product name, description, SKU, "
                    "or category name."
                ),
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description=(
                    "Order results by name, price, created_at, "
                    "or updated_at. Use - before a field for "
                    "descending order."
                ),
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="page",
                description="Page number for pagination.",
                required=False,
                type=int,
            ),
        ],
        responses={
            200: ProductSerializer(many=True),
        },
        tags=["Products"],
    ),

    post=extend_schema(
        summary="Create product",
        description=(
            "Create a new product. Staff permissions are required."
        ),
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: OpenApiResponse(
                description="Invalid product data."
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Staff permissions are required."
            ),
        },
        tags=["Products"],
    ),
)


# =====================================================
# PRODUCT DETAIL DOCUMENTATION
# =====================================================

product_detail_docs = extend_schema_view(
    get=extend_schema(
        summary="Retrieve product",
        description="Retrieve details of a specific product.",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(
                description="Product not found."
            ),
        },
        tags=["Products"],
    ),

    put=extend_schema(
        summary="Update product",
        description="Completely update an existing product. Staff permissions are required.",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(
                description="Invalid product data."
            ),
            403: OpenApiResponse(
                description="Staff permissions are required."
            ),
            404: OpenApiResponse(
                description="Product not found."
            ),
        },
        tags=["Products"],
    ),

    patch=extend_schema(
        summary="Partially update product",
        description="Update selected fields of an existing product. Staff permissions are required.",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(
                description="Invalid product data."
            ),
            403: OpenApiResponse(
                description="Staff permissions are required."
            ),
            404: OpenApiResponse(
                description="Product not found."
            ),
        },
        tags=["Products"],
    ),

    delete=extend_schema(
        summary="Delete product",
        description="Delete an existing product. Staff permissions are required.",
        responses={
            204: OpenApiResponse(
                description="Product deleted successfully."
            ),
            403: OpenApiResponse(
                description="Staff permissions are required."
            ),
            404: OpenApiResponse(
                description="Product not found."
            ),
        },
        tags=["Products"],
    ),
)


# =====================================================
# CATEGORY LIST AND CREATE DOCUMENTATION
# =====================================================

category_list_create_docs = extend_schema_view(
    get=extend_schema(
        summary="List categories",
        description=(
            "Retrieve a paginated list of product categories. "
            "Supports filtering, searching, and ordering."
        ),
        parameters=[
            OpenApiParameter(
                name="is_active",
                description="Filter categories by active status.",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="search",
                description="Search categories by name or description.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description=(
                    "Order categories by name, created_at, "
                    "or updated_at. Use - for descending order."
                ),
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="page",
                description="Page number for pagination.",
                required=False,
                type=int,
            ),
        ],
        responses={
            200: CategorySerializer(many=True),
        },
        tags=["Categories"],
    ),

    post=extend_schema(
        summary="Create category",
        description="Create a new product category. Staff permissions are required.",
        request=CategorySerializer,
        responses={
            201: CategorySerializer,
            400: OpenApiResponse(
                description="Invalid category data."
            ),
            403: OpenApiResponse(
                description="Staff permissions are required."
            ),
        },
        tags=["Categories"],
    ),
)


# =====================================================
# CATEGORY DETAIL DOCUMENTATION
# =====================================================

category_detail_docs = extend_schema_view(
    get=extend_schema(
        summary="Retrieve category",
        description="Retrieve details of a specific category.",
        responses={
            200: CategorySerializer,
            404: OpenApiResponse(
                description="Category not found."
            ),
        },
        tags=["Categories"],
    ),

    put=extend_schema(
        summary="Update category",
        description="Completely update an existing category. Staff permissions are required.",
        request=CategorySerializer,
        responses={
            200: CategorySerializer,
            400: OpenApiResponse(
                description="Invalid category data."
            ),
            403: OpenApiResponse(
                description="Staff permissions are required."
            ),
            404: OpenApiResponse(
                description="Category not found."
            ),
        },
        tags=["Categories"],
    ),

    patch=extend_schema(
        summary="Partially update category",
        description="Update selected fields of an existing category. Staff permissions are required.",
        request=CategorySerializer,
        responses={
            200: CategorySerializer,
            400: OpenApiResponse(
                description="Invalid category data."
            ),
            403: OpenApiResponse(
                description="Staff permissions are required."
            ),
            404: OpenApiResponse(
                description="Category not found."
            ),
        },
        tags=["Categories"],
    ),

    delete=extend_schema(
        summary="Delete category",
        description="Delete an existing category. Deletion is prevented if products still reference it.",
        responses={
            204: OpenApiResponse(
                description="Category deleted successfully."
            ),
            403: OpenApiResponse(
                description="Staff permissions are required."
            ),
            404: OpenApiResponse(
                description="Category not found."
            ),
            500: OpenApiResponse(
                description="Category deletion may be blocked by protected product relationships."
            ),
        },
        tags=["Categories"],
    ),
)
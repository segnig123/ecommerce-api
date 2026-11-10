from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from drf_spectacular.utils import extend_schema, extend_schema_view

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from .permissions import IsStaffOrReadOnly
from .pagination import ProductPagination



# PRODUCT VIEWS

@extend_schema_view(
    get=extend_schema(
        summary="List products",
        description=(
            "Returns a paginated list of products. "
            "Supports filtering by category, price, and active status. "
            "Also supports searching and ordering."
        ),
        tags=["Products"],
    ),
    post=extend_schema(
        summary="Create a product",
        description="Creates a new product. Only staff users can create products.",
        tags=["Products"],
    ),
)
class ProductListCreateView(generics.ListCreateAPIView):

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    # Filtering
    filterset_fields = {
        'category': ['exact'],
        'price': ['exact', 'gte', 'lte'],
        'is_active': ['exact'],
    }

    # Searching
    search_fields = [
        'name',
        'description',
        'sku',
        'category__name',
    ]

    # Ordering
    ordering_fields = [
        'name',
        'price',
        'created_at',
        'updated_at',
    ]

    ordering = ['-created_at']

    pagination_class = ProductPagination


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve a product",
        description="Returns the details of a specific product.",
        tags=["Products"],
    ),
    put=extend_schema(
        summary="Update a product",
        description="Completely updates a product. Only staff users can perform this action.",
        tags=["Products"],
    ),
    patch=extend_schema(
        summary="Partially update a product",
        description="Updates selected fields of a product. Only staff users can perform this action.",
        tags=["Products"],
    ),
    delete=extend_schema(
        summary="Delete a product",
        description="Deletes a product. Only staff users can perform this action.",
        tags=["Products"],
    ),
)
class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrReadOnly]



# CATEGORY VIEWS

@extend_schema_view(
    get=extend_schema(
        summary="List categories",
        description=(
            "Returns a paginated list of product categories. "
            "Supports filtering by active status, searching, and ordering."
        ),
        tags=["Categories"],
    ),
    post=extend_schema(
        summary="Create a category",
        description="Creates a new product category. Only staff users can create categories.",
        tags=["Categories"],
    ),
)
class CategoryListCreateView(generics.ListCreateAPIView):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    # Filtering
    filterset_fields = ['is_active']

    # Searching
    search_fields = [
        'name',
        'description',
    ]

    # Ordering
    ordering_fields = [
        'name',
        'created_at',
        'updated_at',
    ]

    ordering = ['name']

    pagination_class = ProductPagination


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve a category",
        description="Returns the details of a specific product category.",
        tags=["Categories"],
    ),
    put=extend_schema(
        summary="Update a category",
        description="Completely updates a category. Only staff users can perform this action.",
        tags=["Categories"],
    ),
    patch=extend_schema(
        summary="Partially update a category",
        description="Updates selected fields of a category. Only staff users can perform this action.",
        tags=["Categories"],
    ),
    delete=extend_schema(
        summary="Delete a category",
        description="Deletes a category. Only staff users can perform this action.",
        tags=["Categories"],
    ),
)
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrReadOnly]
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from .permissions import IsStaffOrReadOnly
from .pagination import ProductPagination

from .docs import (
    product_list_create_docs,
    product_detail_docs,
    category_list_create_docs,
    category_detail_docs,
)


# PRODUCT VIEWS

@product_list_create_docs
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


@product_detail_docs
class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrReadOnly]



# CATEGORY VIEWS

@category_list_create_docs
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


@category_detail_docs
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrReadOnly]
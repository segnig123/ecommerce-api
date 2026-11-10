from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from .permissions import IsStaffOrReadOnly

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .pagination import ProductPagination

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


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrReadOnly]


class CategoryListCreateView(generics.ListCreateAPIView):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = ['is_active']

    search_fields = [
        'name',
        'description',
    ]

    ordering_fields = [
        'name',
        'created_at',
        'updated_at',
    ]

    ordering = ['name']

    pagination_class = ProductPagination

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrReadOnly]
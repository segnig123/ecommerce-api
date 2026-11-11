from django.urls import path

from .views import (
    CartDetailView,
    AddToCartView,
    CartItemDetailView,
    ClearCartView,
)


urlpatterns = [
    path("", CartDetailView.as_view(), name="cart-detail"),

    path("items/", AddToCartView.as_view(), name="add-to-cart"),

    path(
        "items/<int:pk>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail"
    ),

    path("clear/", ClearCartView.as_view(), name="clear-cart"),
]
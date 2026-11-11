from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from products.models import Product

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)


class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        cart = (
            Cart.objects
            .prefetch_related("items__product")
            .get(pk=cart.pk)
        )

        serializer = CartSerializer(cart)

        return Response(serializer.data)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        product = get_object_or_404(
            Product.objects.select_for_update(),
            id=product_id,
            is_active=True
        )

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        cart_item = (
            CartItem.objects
            .select_for_update()
            .filter(cart=cart, product=product)
            .first()
        )

        current_quantity = cart_item.quantity if cart_item else 0
        new_quantity = current_quantity + quantity

        if new_quantity > product.stock_quantity:
            return Response(
                {
                    "error": "Not enough stock available.",
                    "available_stock": product.stock_quantity,
                    "current_quantity": current_quantity,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if cart_item:
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity
            )

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(
            CartItem.objects.select_related("product", "cart"),
            pk=pk,
            cart__user=request.user
        )

    def patch(self, request, pk):
        cart_item = self.get_object(request, pk)

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data["quantity"]

        if quantity > cart_item.product.stock_quantity:
            return Response(
                {
                    "error": "Not enough stock available.",
                    "available_stock": cart_item.product.stock_quantity,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        return Response(
            CartSerializer(cart_item.cart).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):
        cart_item = self.get_object(request, pk)

        cart = cart_item.cart
        cart_item.delete()

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )


class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = Cart.objects.filter(user=request.user).first()

        if cart is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        cart.items.all().delete()

        return Response(
            {"message": "Cart cleared successfully."},
            status=status.HTTP_200_OK
        )

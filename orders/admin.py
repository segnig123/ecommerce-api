from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Display order items inside their parent order."""

    model = OrderItem
    extra = 0

    fields = (
        "product_name",
        "unit_price",
        "quantity",
        "subtotal",
        "created_at",
    )

    readonly_fields = (
        "product_name",
        "unit_price",
        "subtotal",
        "created_at",
    )

    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Manage customer orders through the Django admin panel."""

    list_display = (
        "order_number",
        "user",
        "status",
        "total_amount",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "items__product_name",
    )

    readonly_fields = (
        "order_number",
        "total_amount",
        "created_at",
        "updated_at",
    )

    inlines = [OrderItemInline]

    ordering = ("-created_at",)

    @admin.display(description="Order Total")
    def get_total(self, obj):
        return obj.total_amount
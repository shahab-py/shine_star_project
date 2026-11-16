
from django.contrib import admin
from .models import Order, OrderItem
from django.utils.html import format_html


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ('price_at_purchase', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'get_full_name',
        'phone_number',
        'paid',
        'display_order_status',
        'created',
    ]

    list_filter = [
        'status',
        'paid',
        'created',
        'city',
        'province',
    ]

    search_fields = ['first_name', 'last_name', 'phone_number']
    inlines = [OrderItemInline]
    ordering = ['-created']
    list_per_page = 20

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    get_full_name.short_description = 'نام و نام خانوادگی'

    @admin.display(description='وضعیت سفارش')
    def display_order_status(self, obj):
        status_colors = {
            'pending': 'orange',
            'paid': 'green',
            'processing': 'blue',
            'shipped': 'blue',
            'delivered': 'green',
            'cancelled': 'red',
            'expired': 'gray',
            'payment_review': 'darkorange',
        }

        color = status_colors.get(obj.status, 'black')
        text = obj.get_status_display()

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            text,
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        readonly.extend(['paid', 'status'])
        return readonly
from django.contrib import admin
from .models import Order, OrderItem
from django.utils.html import format_html

# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['price_at_purchase']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = ['id', 'get_full_name', 'phone_number', 'paid', 'display_paid_status', 'created']
    list_filter = ['paid', 'created', 'city', 'province']
    list_editable = ['paid']
    search_fields = ['first_name', 'last_name', 'phone_number']
    inlines = [OrderItemInline]
    ordering = ['-created']
    list_per_page = 20

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'نام و نام خانوادگی'

    def display_paid_status(self, obj):
        color = 'green' if obj.paid else 'red'
        text = '✅ پرداخت شده' if obj.paid else '❌ پرداخت نشده'
        return format_html('<span style="color: {};">{}</span>', color, text)
    display_paid_status.short_description = 'وضعیت (رنگی)'
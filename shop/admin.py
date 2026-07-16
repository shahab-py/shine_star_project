from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['price_at_purchase']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'get_product_count']
    prepopulated_fields = {'slug': ('name',)}

    def get_product_count(self, obj):
        return obj.products.count()
    get_product_count.short_description = 'تعداد محصولات'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'status_tag', 'is_available']
    list_filter = ['is_available', 'category', 'created']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock', 'is_available']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20

    def display_price(self, obj):
        return f"{obj.price:,.0f} تومان"
    display_price.short_description = 'قیمت'

    def status_tag(self, obj):
        color = 'green' if obj.stock > 0 else 'red'
        text = 'موجود' if obj.stock > 0 else 'ناموجود'
        return format_html('<b style="color: {};">{}</b>', color, text)
    status_tag.short_description = 'وضعیت انبار'


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
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product
from orders.models import Order, OrderItem

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
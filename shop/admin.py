from django.contrib import admin
from .models import Category, Product, Order, OrderItem
from django.utils.html import format_html


# نمایش محصولات داخل صفحه سفارش
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price_display', 'stock', 'is_available']
    list_filter = ['is_available', 'category', 'created']
    search_fields = ['name', 'description']
    list_editable = ['stock', 'is_available']
    prepopulated_fields = {'slug': ('name',)}

    def price_display(self, obj):
        return format_html("{}", "{:,.0f}".format(obj.price))

    price_display.short_description = 'قیمت'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'phone_number', 'email', 'paid', 'created']
    list_filter = ['paid', 'created', 'city', 'province']
    list_editable = ['paid']
    search_fields = ['full_name', 'phone']
    inlines = [OrderItemInline]
    ordering = ['-created']


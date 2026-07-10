from django.contrib import admin
from .models import Category, Product, Order, OrderItem

# نمایش محصولات داخل صفحه سفارش
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)} # خودکار اسلاگ را بر اساس نام می‌سازد

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # اصلاح شد: از is_available استفاده شد
    list_display = ['name', 'category', 'price', 'stock', 'is_available']
    list_filter = ['is_available', 'category', 'created']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock', 'is_available']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'phone_number', 'email', 'paid', 'created']
    list_filter = ['paid', 'created', 'city', 'province']
    list_editable = ['paid']
    search_fields = ['full_name', 'phone']
    inlines = [OrderItemInline]
    ordering = ['-created']


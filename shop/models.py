from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(unique=True, blank=True, verbose_name="اسلاگ")

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="دسته‌بندی")
    name = models.CharField(max_length=200, verbose_name="نام محصول")
    slug = models.SlugField(unique=True, blank=True, verbose_name="اسلاگ")
    description = models.TextField(verbose_name="توضیحات محصول")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="قیمت (تومان)")
    stock = models.PositiveIntegerField(default=0, verbose_name="موجودی انبار")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="تصویر محصول")
    is_available = models.BooleanField(default=True, verbose_name="قابل فروش")
    created = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

    def __str__(self):
        return self.name


class Order(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="نام")
    last_name = models.CharField(max_length=50, verbose_name="نام خانوادگی")
    email = models.EmailField(verbose_name="ایمیل")
    address = models.CharField(max_length=255, verbose_name="آدرس")
    city = models.CharField(max_length=100, verbose_name="شهر")
    postcode = models.CharField(max_length=10, verbose_name="کد پستی")
    phone_number = models.CharField(max_length=11, verbose_name="شماره تماس")
    province = models.CharField(max_length=50, blank=True, null=True, verbose_name="استان")
    created = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ سفارش")
    paid = models.BooleanField(default=False, verbose_name="پرداخت شده")

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"

    def __str__(self):
        return f"Order #{self.id} - {self.first_name} {self.last_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price_at_purchase = models.DecimalField(
            max_digits=12, 
            decimal_places=0, 
            null=True, 
            blank=True, 
            verbose_name="قیمت در لحظه خرید"
        )
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
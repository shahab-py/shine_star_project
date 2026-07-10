from django.db import models

class Category(models.Model):
    name = models.CharField(max_length = 100, verbose_name = "نام دسته بندی ")
    slug = models.SlugField(unique = True, blank = True)

    class Meta:
        verbose_name_plural ="دسته بندی ها"

    def __str__(self):
        return self.name
    

class Product(models.Model):
    category = models.ForeignKey(Category,on_delete=models.CASCADE, related_name = 'products', verbose_name ="دسته بندی" )
    name = models.CharField(max_length=200, verbose_name = "نام محصول")
    slug = models.SlugField(unique = True, blank = True)
    description = models.TextField(verbose_name = "توضیحات محصول")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name ="قیمت:")
    stock = models.IntegerField(default = 0, verbose_name = "موجودی انبار")
    image = models.ImageField(upload_to='products/', null = True, blank = True)
    is_available = models.BooleanField(default = True, verbose_name = "قابل فروش")
    created = models.DateTimeField(auto_now_add=True, verbose_name = "تاریخ شارژ")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "محصولات"


# shop/models.py

class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=11)
    created = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False) 
    province = models.CharField(max_length=50, blank=True, null=True) 

    def __str__(self):
        return f"Order {self.id} by {self.first_name}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)



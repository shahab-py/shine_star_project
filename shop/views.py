from django.shortcuts import render, redirect
from .models import OrderItem
from .forms import OrderCreateForm
from .models import Product
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from .cart import Cart

def product_list(request):
    products = Product.objects.filter(is_available = True)
    return render(request, 'shop/product_list.html', {'products':products})


def home(request):
    products = Product.objects.all() 
    return render(request, 'shop/home.html', {'products': products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})


def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1)
    

    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/templatetags/price_tags.html', {'cart': cart})


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')



# shop/views.py
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # ۱. ذخیره اطلاعات سفارش در مدل Order
            # چون مدل را در مرحله قبل اصلاح کردیم، حالا این خط خطا نمی‌دهد
            order = form.save()

            # ۲. انتقال آیتم‌ها از سبد خرید به OrderItem
            # دقت کن: در فایل اول دیدم که از cart.items.items() استفاده کردی
            # پس باید مطابق همان ساختار بنویسیم
            for product, quantity in cart.items.items():
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price,  # ذخیره قیمت محصول در لحظه خرید
                    quantity=quantity
                )
                # ۳. کاهش موجودی انبار
                product.stock -= quantity
                product.save()

            # ۴. خالی کردن سبد خرید
            cart.clear()

            # ۵. هدایت به صفحه موفقیت
            return render(request, 'shop/orders/created.html', {'order': order})
    else:
        form = OrderCreateForm()
    
    return render(request, 'shop/orders/create.html', {'cart': cart, 'form': form})




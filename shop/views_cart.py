from django.shortcuts import render, get_object_or_404, redirect
from .cart import Cart
from .models import Product
from django.contrib import messages
from django.http import HttpResponse

def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1)
    

    return redirect('shop:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart_detail.html', {'cart': cart})


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:cart_detail')

def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 0))
        except ValueError:
            quantity = 0

        if quantity > product.stock:
            messages.error(request, f"موجودی {product.name} محدود است. حداکثر {product.stock} عدد.")
            quantity = product.stock

        if quantity > 0:
            cart.add(product, override_quantity=quantity)
        else:
            cart.remove(product)


    return redirect('shop:cart_detail') 


def checkout_view(request):
    cart = Cart(request)

    is_valid, error_message = cart.validate_stock()
    
    if not is_valid:
        messages.error(request, error_message)
        return redirect('shop:cart_detail')

    if request.method == 'POST':
        pass

    context = {
        'cart': cart,
        'total_price': cart.get_total_price(),
    }
    
    return render(request, 'shop/checkout.html', context)





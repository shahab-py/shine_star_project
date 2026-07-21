from django.shortcuts import render, redirect
from .models import OrderItem
from .forms import OrderCreateForm
from .models import Product
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse
from .cart import Cart
from django.db import connection

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
    return render(request, 'shop/cart_detail.html', {'cart': cart})


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')


def order_create(request):
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            cart = Cart(request)
            
            items_to_process = []
            for item in cart.items.values():
                items_to_process.append({
                    'product': item['product'],
                    'price': item['price'],
                    'quantity': item['quantity']
                })
            order = form.save()

            for item in items_to_process:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price_at_purchase=item['price'],
                    quantity=item['quantity']
                )
                product = item['product']
                product.stock -= item['quantity']
                product.save()
            request.session.flush()
            print(f"DEBUG: Session flushed. Current session keys: {request.session.keys()}")

            request.session.create() 
            
            if 'cart' in request.session:
                del request.session['cart']
            if request.session.session_key:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM django_session WHERE session_key = %s", 
                        [request.session.session_key]
                    )


            return redirect('shop:order_complete')
    else:
        form = OrderCreateForm()
    
    cart = Cart(request)
    return render(request, 'shop/orders/create.html', {'cart': cart, 'form': form})
from django.shortcuts import render, redirect
from .models import OrderItem
from .forms import OrderCreateForm
from .models import Product
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse
from .cart import Cart
from django.db import transaction

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
    

    return redirect('shop:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart_detail.html', {'cart': cart})


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:cart_detail')


from django.db import transaction

def order_create(request):
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cart = Cart(request)
                    
                    order = form.save()

                    for item in cart.items.values():
                        product = item['product']
                        quantity = item['quantity']
                        price = item['price']

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            price_at_purchase=price,
                            quantity=quantity
                        )
                        
                        product.stock -= quantity
                        product.save()

                    if 'cart' in request.session:
                        del request.session['cart']
                    

                return redirect('shop:order_complete')
                
            except Exception as e:
                print(f"ERROR during order creation: {e}")
    else:
        form = OrderCreateForm()
    
    cart = Cart(request)
    return render(request, 'shop/orders/create.html', {'cart': cart, 'form': form})

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
    return render(request, 'shop/cart_detail.html', {'cart': cart})


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            items_to_process = cart.items
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

            cart.clear() 
            request.session.save()
            return redirect('shop:order_create')
    else:
        form = OrderCreateForm()
    
    return render(request, 'shop/orders/create.html', {'cart': cart, 'form': form})




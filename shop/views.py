from django.shortcuts import render, redirect
from orders.models import OrderItem
from orders.forms import OrderCreateForm
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


from django.shortcuts import render
from django.db import transaction
from django.shortcuts import render, redirect
from .models import OrderItem
from .forms import OrderCreateForm
from shop.models import Product
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse
from shop.cart import Cart
from .models import Order
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


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
from django.contrib import messages

@transaction.atomic
def order_create(request):
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                cart = Cart(request)
                order = form.save()

                for item_data in cart.items.values():
                    product = item_data['product']
                    quantity = item_data['quantity']
                    price = item_data['price']

                    if product.stock < quantity:
                        raise ValueError(f"محصول '{product.name}' در انبار موجود نیست.")

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
                
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, "خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید.")
                print(f"CRITICAL ERROR: {e}")
    else:
        form = OrderCreateForm()
    
    cart = Cart(request)
    return render(request, 'shop/orders/create.html', {'cart': cart, 'form': form})

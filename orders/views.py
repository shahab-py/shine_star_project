from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import OrderItem, Order
from .forms import OrderCreateForm
from shop.cart import Cart
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
import requests
from django.http import HttpResponse , response
from django.conf import settings



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
                
                return redirect('orders:order_complete')
                
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, "خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید.")
                print(f"CRITICAL ERROR: {e}")
    else:
        form = OrderCreateForm()
    
    cart = Cart(request)
    return redirect('orders:payment_start', order_id=order.id)



MERCHANT_ID = 'a0000000-0000-0000-0000-000000000000' 

def payment_start(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    payload = {
        'merchant_id': settings.MERCHANT_ID,
        'amount': int(order.total_price),  
        'description': f"پرداخت سفارش شماره {order.id}",
        'callback_url': request.build_absolute_uri(reverse('orders:payment_verify', args=[order.id])),
        'metadata': {'order_id': str(order.id)},
    }

    try:
        response = requests.post(settings.ZARINPAL_START_URL, json=payload)
        result = response.json()
        print(f"DEBUG: Zarinpal Start Response: {result}")

        data_payload = result.get('data')
        
        if data_payload is not None and isinstance(data_payload, dict):
            code = data_payload.get('code')
            
            if code in [100, 101]:
                authority = data_payload.get('authority')
                if authority:

                    payment_url = data_payload.get('url') 
                    if not payment_url:
                        payment_url = f"https://www.zarinpal.com/pg/StartPay/{authority}"
                    
                    return redirect(payment_url)
                else:
                    messages.error(request, "شناسه تراکنش (Authority) یافت نشد.")
            else:

                error_info = result.get('errors')
                if error_info and isinstance(error_info, list) and len(error_info) > 0:
                    error_msg = error_info[0].get('message', 'خطای نامشخص')
                else:
                    error_msg = data_payload.get('message', 'خطای نامشخص در درگاه')
                
                messages.error(request, f"خطا در پرداخت: {error_msg}")
        else:
            messages.error(request, "پاسخ نامعتبر از سمت درگاه دریافت شد.")

        return redirect('shop:cart_detail')

    except Exception as e:
        print(f"Payment System Error: {e}")
        messages.error(request, "خطای سیستمی در اتصال به بانک.")
        return redirect('shop:cart_detail')


def payment_verify(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    authority = request.GET.get('Authority')

    if not authority:
        messages.error(request, "شناسه تراکنش یافت نشد.")
        return redirect('shop:home')

    verify_data = {
        'merchant_id': settings.MERCHANT_ID, 
        'amount': int(order.total_price),
        'authority': authority,
    }

    try:
        url = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'
        
        response = requests.post(url, json=verify_data)
        result = response.json()
        
        print(f"DEBUG: Verify Data: {verify_data}")
        print(f"DEBUG: Zarinpal Response: {result}")
        if result.get('data') and result.get('data', {}).get('code') in [100, 101]:
            order.paid = True
            order.save()
            messages.success(request, "پرداخت موفق بود.")
            return redirect('orders:order_success') 
        else:
            error_msg = result.get('errors', {}).get('message', 'خطای نامشخص')
            messages.error(request, f"پرداخت تایید نشد: {error_msg}")
            return redirect('shop:cart_detail')

    except Exception as e:
        print(f"Verification System Error: {e}")
        return redirect('shop:cart_detail')

from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
import requests
from .models import Order, OrderItem
from .forms import OrderCreateForm
from shop.cart import Cart



merchant_id = settings.ZARINPAL['MERCHANT_ID']

@transaction.atomic
def order_create(request):
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                cart = Cart(request)
                if not cart:
                    messages.warning(request, "سبد خرید شما خالی است.")
                    return redirect('shop:cart_detail')

                order = form.save()
                total_order_price = 0

                for item in cart:
                    product = item['product']
                    quantity = item['quantity']
                    price = item.get('price', 0)
                    if product.stock < quantity:
                        raise ValueError(f"متاسفانه موجودی محصول '{product.name}' کافی نیست.")

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price_at_purchase=price,
                        quantity=quantity
                    )
                    total_order_price += (price * quantity)

                order.total_price = total_order_price
                order.save()

                cart.clear()
                request.session['last_order_id'] = order.id
                return redirect('orders:payment_start', order_id=order.id)

            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                print(f"CRITICAL ERROR in order_create: {e}")
                messages.error(request, "خطایی در ثبت سفارش رخ داد.")
        else:
            messages.error(request, "اطلاعات فرم صحیح نیست.")
    else:
        form = OrderCreateForm()
    return render(request, 'orders/orders/create.html', {'form': form})


@transaction.atomic
def payment_verify(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    authority = request.GET.get('Authority')

    if not authority:
        messages.error(request, "شناسه تراکنش یافت نشد.")
        return redirect('shop:home')

    verify_payload = {
        'merchant_id': settings.ZARINPAL['MERCHANT_ID'],
        'amount': int(order.total_price),
        'authority': authority,
    }

    try:
        response = requests.post(settings.ZARINPAL['VERIFY_URL'], json=verify_payload, timeout=10)
        result = response.json()

        # بررسی موفقیت در درگاه
        if result.get('data') and result.get('data', {}).get('code') in [100, 101]:
            
            for item in order.items.all():
                product = item.product
                if product.stock < item.quantity:
                    raise ValueError(f"متاسفانه در لحظه پرداخت، موجودی {product.name} تمام شد.")
                
                product.stock -= item.quantity
                product.save()

            order.paid = True
            order.status = 'paid'
            order.save()
            
            messages.success(request, "پرداخت با موفقیت انجام شد.")
            return redirect('orders:order_success')
        
        else:
            # مدیریت پرداخت ناموفق
            error_msg = result.get('errors', {}).get('message', "پرداخت ناموفق بود.")
            messages.error(request, f"پرداخت تایید نشد: {error_msg}")
            return redirect('shop:cart_detail')

    except ValueError as ve:
        messages.error(request, str(ve))
        return redirect('shop:cart_detail')
    except Exception as e:
        print(f"Verification System Error: {e}")
        messages.error(request, "خطا در تایید پرداخت.")
        return redirect('shop:cart_detail')


@transaction.atomic
def payment_start(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    payload = {
        'merchant_id': settings.ZARINPAL['MERCHANT_ID'],
        'amount': int(order.total_price),
    }

    try:
        response = requests.post(settings.ZARINPAL['START_URL'], json=payload, timeout=10)
        result = response.json()

        if result.get('data') and result.get('data', {}).get('code') == 100:
            authority = result['data']['authority']
            zarinpal_url = result['data']['url']
            return redirect(zarinpal_url)
        else:
            error_msg = result.get('errors', {}).get('message', "خطا در شروع پرداخت.")
            messages.error(request, error_msg)
            return redirect('shop:cart_detail')

    except Exception as e:
        print(f"Payment Start Error: {e}")
        messages.error(request, "خطایی در اتصال به درگاه رخ داد.")
        return redirect('shop:cart_detail')


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
    """
    ایجاد سفارش از روی سبد خرید. 
    استفاده از transaction.atomic تضمین می‌کند که اگر موجودی کالا کم بود، 
    سفارش اصلاً ثبت نشود.
    """
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

                    product.stock -= quantity
                    product.save()

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
                messages.error(request, "خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید.")
        else:
            messages.error(request, "لطفاً اطلاعات فرم را به درستی وارد کنید.")
    else:
        form = OrderCreateForm()

    return render(request, 'orders/orders/create.html', {'form': form})


# --- بخش درگاه پرداخت ---

def payment_start(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    payload = {
        'merchant_id': settings.ZARINPAL['MERCHANT_ID'],
        'amount': int(order.total_price),
        'description': f"پرداخت سفارش شماره {order.id}",
        'callback_url': request.build_absolute_uri(reverse('orders:payment_verify', args=[order.id])),
        'metadata': {'order_id': str(order.id)},
    }

    try:
        response = requests.post(settings.ZARINPAL['START_URL'], json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        data_payload = result.get('data')
        
        if data_payload and data_payload.get('code') in [100, 101]:
            authority = data_payload.get('authority')
            payment_url = data_payload.get('url')

            if not payment_url:
                payment_url = f"https://www.zarinpal.com/pg/StartPay/{authority}"
            
            return redirect(payment_url)
        else:
            error_msg = "خطا در ارتباط با درگاه پرداخت."
            if 'errors' in result:
                error_msg = result['errors'][0].get('message', error_msg)
            messages.error(request, f"درگاه پاسخ نداد: {error_msg}")
            return redirect('shop:cart_detail')

    except Exception as e:
        print(f"Payment System Error: {e}")
        messages.error(request, "خطای سیستمی در اتصال به بانک. لطفاً دقایقی دیگر تلاش کنید.")
        return redirect('shop:cart_detail')


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

        if result.get('data') and result.get('data', {}).get('code') in [100, 101]:
            with transaction.atomic():
                order.paid = True
                order.save()
            
            messages.success(request, "پرداخت با موفقیت انجام شد. سفارش شما در حال آماده‌سازی است.")
            return redirect('orders:order_success')
        else:
            error_msg = "پرداخت ناموفق بود."
            if 'errors' in result:
                error_msg = result['errors'].get('message', error_msg)
            messages.error(request, f"پرداخت تایید نشد: {error_msg}")
            return redirect('shop:cart_detail')

    except Exception as e:
        print(f"Verification System Error: {e}")
        messages.error(request, "خطا در تایید پرداخت. لطفاً با پشتیبانی تماس بگیرید.")
        return redirect('shop:cart_detail')

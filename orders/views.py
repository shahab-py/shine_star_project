import logging
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views import View
from django.http import HttpResponseRedirect

from .models import Order, OrderItem
from shop.models import Product
from shop.cart import Cart


logger = logging.getLogger(__name__)

def order_create(request):
    cart = Cart(request)
    if not cart.is_empty():
        user = request.user if request.user.is_authenticated else None

        order = Order.objects.create(
            user=user,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            postcode=request.POST.get('postcode', ''),
            phone_number=request.POST.get('phone_number', ''),
            province=request.POST.get('province', ''),
            status='pending',
            paid=False,
            total_price=cart.get_total_price()
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price_at_purchase=item['price'],
                quantity=item['quantity']
            )

        cart.clear()

        return redirect('orders:payment_start', order_id=order.id)
    
    messages.error(request, "سبد خرید شما خالی است.")
    return redirect('shop:product_list')


def payment_start(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.paid:
        messages.info(request, "این سفارش قبلاً پرداخت شده است.")
        return redirect('orders:order_success', order_id=order.id)

    return redirect('orders:payment_verify', order_id=order.id)

@transaction.atomic
def payment_verify(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.paid:
        return redirect('orders:order_success', order_id=order.id)

    payment_success = True 

    if payment_success:
        try:
            for item in order.items.all():
                product = item.product
                if product.stock < item.quantity:
                    raise ValueError(f"موجودی {product.name} کافی نیست.")
                product.decrease_stock(item.quantity)
                product.save()

            order.paid = True
            order.status = 'paid'
            order.save()
            
            messages.success(request, "پرداخت موفق بود.")
            return redirect('orders:order_success', order_id=order.id)

        except Exception as e:
            logger.error(f"خطا: {str(e)}")
            messages.error(request, f"خطا در تایید نهایی: {str(e)}")
            return redirect('shop:product_list')
    else:
        messages.error(request, "پرداخت ناموفق بود.")
        return redirect('shop:product_list')



def order_success(request, order_id):

    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_success.html', {'order': order})

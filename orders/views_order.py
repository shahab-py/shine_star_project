# orders/views_order.py

from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import OrderCreateForm
from .models import Order, OrderItem
from shop.cart import Cart
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages


class OrderCreateView(FormView):
    template_name = 'orders/orders/create.html'
    form_class = OrderCreateForm

    def form_valid(self, form):
        with transaction.atomic():
            cart = Cart(self.request)

            if len(cart) == 0:
                messages.error(self.request, "سبد خرید شما خالی است.")
                return redirect('shop:product_list')

            order = Order.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                email=form.cleaned_data.get('email'),
                address=form.cleaned_data.get('address'),
                city=form.cleaned_data.get('city'),
                postcode=form.cleaned_data.get('postcode'),
                phone_number=form.cleaned_data.get('phone_number'),
                province=form.cleaned_data.get('province'),
                status='pending',
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

    def order_success(request):
        order_id = request.session.get('order_id')
        order = get_object_or_404(Order, id=order_id) if order_id else None
        return render(request, 'orders/order_success.html', {'order': order})

# orders/views_order.py

from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import OrderCreateForm
from .models import Order, OrderItem
from shop.cart import Cart
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse 

class OrderCreateView(FormView):
    template_name = 'orders/orders/create.html'
    form_class = OrderCreateForm
    success_url = reverse_lazy('orders:order_success')

    def form_valid(self, form):
        cart = Cart(self.request)
        
        try:
            with transaction.atomic():
                order = form.save()
                total_order_price = 0 

                for item in cart:
                    product = item['product']
                    quantity_to_buy = item['quantity']
                    item_price = item.get('price', 0) 

                    print(f"DEBUG: Product: {product.name}, Price: {item_price}, Qty: {quantity_to_buy}")

                    if product.stock < quantity_to_buy:
                        raise ValidationError(f"متاسفانه موجودی محصول '{product.name}' کافی نیست.")

                    line_total = item_price * quantity_to_buy
                    total_order_price += line_total 

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price_at_purchase=item_price,
                        quantity=quantity_to_buy
                    )

                    product.stock -= quantity_to_buy
                    product.save()

                order.total_price = total_order_price
                order.save()
                print(f"DEBUG: Final Total Price saved to Order: {total_order_price}")

                cart.clear() 
                self.request.session['order_id'] = order.id

            return super().form_valid(form) 

        except ValidationError as e:
            form.add_error(None, e.message)
            return self.render_to_response(self.get_context_data(form=form))

        except Exception as e:
            form.add_error(None, f"خطایی در ثبت سفارش رخ داد: {str(e)}")
            # response = self.form_invalid(form)
            # return response
            return self.render_to_response(self.get_context_data(form=form))


def order_success(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id) if order_id else None
    return render(request, 'orders/order_success.html', {'order': order})

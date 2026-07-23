from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import OrderCreateForm
from .models import Order, OrderItem
from shop.cart import Cart
from django.shortcuts import render
from django.db import transaction
from django.core.exceptions import ValidationError




class OrderCreateView(FormView):
    template_name = 'orders/orders/create.html'
    form_class = OrderCreateForm
    success_url = reverse_lazy('orders:order_success')

    def form_valid(self, form):
        cart = Cart(self.request)
        
        try:
            with transaction.atomic():
                order = form.save()

                for item in cart:
                    product = item['product']
                    quantity_to_buy = item['quantity']

                    if product.stock < quantity_to_buy:
                        raise ValidationError(f"متاسفانه موجودی محصول '{product.name}' کافی نیست.")

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price_at_purchase=item['price'],
                        quantity=quantity_to_buy
                    )
                    
                    product.stock -= quantity_to_buy
                    product.save()

                cart.clear() 

            return super().form_valid(form)

        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)
        except Exception as e:
            # برای خطاهای دیگر
            form.add_error(None, f"خطایی در ثبت سفارش رخ داد: {str(e)}")
            return self.form_invalid(form)
    

def order_success(request):
    return render(request, 'orders/order_success.html')
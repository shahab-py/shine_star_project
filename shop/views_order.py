from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import OrderCreateForm
from .models import Order, OrderItem
from .cart import Cart

class OrderCreateView(FormView):
    template_name = 'shop/orders/create.html'
    form_class = OrderCreateForm
    success_url = reverse_lazy('order_success')

    def form_valid(self, form):
        cart = Cart(self.request)
    
        if not cart:
            return super().form_valid(form)

   
        order = Order.objects.create(
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            email=form.cleaned_data['email'],
            address=form.cleaned_data['address'],
            city=form.cleaned_data['city'],
            postcode=form.cleaned_data['postcode'],
            phone_number=form.cleaned_data['phone_number'],
        )



  
        

        return super().form_valid(form)
    
        for item in cart:
            order_item = OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                quantity=item['quantity']
            )
  
            item['product'].stock -= item['quantity']
            item['product'].save()

            cart.clear()


from django.views.generic import TemplateView

class OrderSuccessView(TemplateView):
    template_name = 'shop/orders/created.html'



from django.shortcuts import render

def order_success(request):
    return render(request, 'shop/order_success.html')

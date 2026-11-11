
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from django.core.exceptions import ValidationError
from django.contrib import messages

from .forms import OrderCreateForm
from .services import create_order_from_cart


class OrderCreateView(FormView):
    template_name = 'orders/orders/create.html'
    form_class = OrderCreateForm

    def form_valid(self, form):
        try:
            order = create_order_from_cart(
                request=self.request,
                customer_data=form.cleaned_data,
            )

        except ValidationError as exc:
            messages.error(
                self.request,
                " ".join(exc.messages)
            )
            return redirect('shop:product_list')

        return redirect(
            'orders:payment_start',
            order_id=order.id
        )

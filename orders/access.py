
from django.http import Http404

from .models import Order


def get_accessible_order(request, order_id):
    order = Order.objects.filter(id=order_id).first()

    if order is None:
        raise Http404("سفارش پیدا نشد.")

    if order.user_id is not None:
        if (
            not request.user.is_authenticated
            or order.user_id != request.user.id
        ):
            raise Http404("سفارش پیدا نشد.")

        return order

    guest_order_ids = request.session.get(
        "guest_order_ids",
        [],
    )

    if order.id not in guest_order_ids:
        raise Http404("سفارش پیدا نشد.")

    return order

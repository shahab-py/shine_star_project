
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Order, OrderItem
from shop.models import Product
from shop.cart import Cart


@transaction.atomic
def create_order_from_cart(request, customer_data):
    cart = Cart(request)

    cart_items = cart.cart.copy()

    if not cart_items:
        raise ValidationError("سبد خرید خالی است.")

    product_ids = [int(product_id) for product_id in cart_items]

    products = Product.objects.select_for_update().filter(
        id__in=product_ids
    )

    products_by_id = {
        product.id: product
        for product in products
    }

    if len(products_by_id) != len(product_ids):
        raise ValidationError("یکی از محصولات سبد خرید دیگر موجود نیست.")

    total_price = Decimal("0")

    validated_items = []

    for product_id, cart_item in cart_items.items():
        product = products_by_id[int(product_id)]
        try:
            quantity = int(cart_item["quantity"])

        except (ValueError, TypeError, KeyError):
            raise ValidationError(
                "تعداد یکی از محصولات سبد خرید معتبر نیست."
            )

        if quantity <= 0:
            raise ValidationError("تعداد محصول معتبر نیست.")

        if not product.is_available:
            raise ValidationError(
                f"محصول {product.name} قابل فروش نیست."
            )

        if product.stock < quantity:
            raise ValidationError(
                f"موجودی محصول {product.name} کافی نیست."
            )

        total_price += product.price * quantity

        validated_items.append({
            "product": product,
            "price": product.price,
            "quantity": quantity,
        })

    order = Order.objects.create(
        user=(
            request.user
            if request.user.is_authenticated
            else None
        ),
        first_name=customer_data["first_name"],
        last_name=customer_data["last_name"],
        email=customer_data["email"],
        address=customer_data["address"],
        city=customer_data["city"],
        postcode=customer_data["postcode"],
        phone_number=customer_data["phone_number"],
        province=customer_data.get("province"),
        status="pending",
        total_price=total_price,
    )

    for item in validated_items:
        OrderItem.objects.create(
            order=order,
            product=item["product"],
            price_at_purchase=item["price"],
            quantity=item["quantity"],
        )

    return order

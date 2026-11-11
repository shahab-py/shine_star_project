
import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from shop.cart import Cart
from shop.factories import ProductFactory

from orders.services import create_order_from_cart
from orders.models import Order, OrderItem


@pytest.mark.django_db
def test_create_order_success():
    product = ProductFactory(
        price=100000,
        stock=10,
        is_available=True,
    )

    request = RequestFactory().post("/orders/create/")
    request.user = AnonymousUser()

    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    cart = Cart(request)
    cart.add(product, quantity=2)

    customer_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "address": "Test Address",
        "city": "Tehran",
        "postcode": "1234567890",
        "phone_number": "09123456789",
    }

    order = create_order_from_cart(request, customer_data)

    assert Order.objects.count() == 1
    assert OrderItem.objects.filter(order=order).count() == 1

    assert order.total_price == 200000
    assert order.status == "pending"
    assert order.paid is False

    order_item = order.items.first()

    assert order_item.product == product
    assert order_item.quantity == 2
    assert order_item.price_at_purchase == 100000

    assert product.stock == 10
    assert len(Cart(request)) == 2


@pytest.mark.django_db
def test_create_order_with_empty_cart():
    request = RequestFactory().post("/orders/create/")
    request.user = AnonymousUser()

    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    customer_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "address": "Test Address",
        "city": "Tehran",
        "postcode": "1234567890",
        "phone_number": "09123456789",
    }

    with pytest.raises(ValidationError):
        create_order_from_cart(request, customer_data)

    assert Order.objects.count() == 0

@pytest.mark.django_db
def test_create_order_with_unavailable_product():
    product = ProductFactory(
        price=100000,
        stock=10,
        is_available=False,
    )

    request = RequestFactory().post("/orders/create/")
    request.user = AnonymousUser()

    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    cart = Cart(request)
    cart.add(product, quantity=1)

    customer_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "address": "Test Address",
        "city": "Tehran",
        "postcode": "1234567890",
        "phone_number": "09123456789",
    }

    with pytest.raises(ValidationError):
        create_order_from_cart(request, customer_data)

    assert Order.objects.count() == 0

@pytest.mark.django_db
def test_create_order_with_insufficient_stock():
    product = ProductFactory(
        price=100000,
        stock=2,
        is_available=True,
    )

    request = RequestFactory().post("/orders/create/")
    request.user = AnonymousUser()

    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    cart = Cart(request)
    cart.add(product, quantity=3)

    customer_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "address": "Test Address",
        "city": "Tehran",
        "postcode": "1234567890",
        "phone_number": "09123456789",
    }

    with pytest.raises(ValidationError):
        create_order_from_cart(request, customer_data)

    assert Order.objects.count() == 0

@pytest.mark.django_db
def test_create_order_with_deleted_product():
    product = ProductFactory(
        price=100000,
        stock=10,
        is_available=True,
    )

    request = RequestFactory().post("/orders/create/")
    request.user = AnonymousUser()

    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    cart = Cart(request)
    cart.add(product, quantity=1)

    # شبیه‌سازی حذف محصول بعد از اضافه شدن به سبد خرید
    product.delete()

    customer_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "address": "Test Address",
        "city": "Tehran",
        "postcode": "1234567890",
        "phone_number": "09123456789",
    }

    with pytest.raises(ValidationError):
        create_order_from_cart(request, customer_data)

    assert Order.objects.count() == 0

@pytest.mark.django_db
def test_create_order_with_invalid_quantity():
    product = ProductFactory(
        price=100000,
        stock=10,
        is_available=True,
    )

    request = RequestFactory().post("/orders/create/")
    request.user = AnonymousUser()

    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    request.session["cart"] = {
        str(product.id): {
            "quantity": "abc"
        }
    }
    request.session.save()

    customer_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "address": "Test Address",
        "city": "Tehran",
        "postcode": "1234567890",
        "phone_number": "09123456789",
    }

    with pytest.raises(ValidationError):
        create_order_from_cart(request, customer_data)

    assert Order.objects.count() == 0
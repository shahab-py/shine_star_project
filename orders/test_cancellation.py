
import pytest
from django.urls import reverse
from django.utils import timezone

from orders.factories import OrderFactory
from shop.factories import ProductFactory
from orders.models import OrderItem


@pytest.mark.django_db
def test_owner_can_cancel_pending_order(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="owner",
        email="owner@example.com",
        password="test123",
    )

    order = OrderFactory(
        user=user,
        status="pending",
        paid=False,
        payment_authority="",
        payment_request_started_at=None,
    )

    client.force_login(user)

    response = client.post(
        reverse("orders:order_cancel", kwargs={"order_id": order.id})
    )

    order.refresh_from_db()

    assert response.status_code == 302
    assert order.status == "cancelled"
    assert order.paid is False


@pytest.mark.django_db
def test_guest_can_cancel_own_session_order(client):
    order = OrderFactory(
        user=None,
        status="pending",
        paid=False,
        payment_authority="",
        payment_request_started_at=None,
    )

    session = client.session
    session["guest_order_ids"] = [order.id]
    session.save()

    response = client.post(
        reverse("orders:order_cancel", kwargs={"order_id": order.id})
    )

    order.refresh_from_db()

    assert response.status_code == 302
    assert order.status == "cancelled"


@pytest.mark.django_db
def test_other_user_cannot_cancel_order(client, django_user_model):
    owner = django_user_model.objects.create_user(
        username="owner2",
        email="owner2@example.com",
        password="test123",
    )

    other_user = django_user_model.objects.create_user(
        username="other",
        email="other@example.com",
        password="test123",
    )

    order = OrderFactory(user=owner, status="pending")

    client.force_login(other_user)

    response = client.post(
        reverse("orders:order_cancel", kwargs={"order_id": order.id})
    )

    order.refresh_from_db()

    assert response.status_code == 404
    assert order.status == "pending"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "order_data",
    [
        {"paid": True},
        {"status": "expired"},
        {"status": "cancelled"},
        {"payment_request_started_at": timezone.now()},
        {"payment_authority": "A00000000000000000000000000000000000"},
    ],
)
def test_ineligible_order_cannot_be_cancelled(
    client,
    django_user_model,
    order_data,
):
    user = django_user_model.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="test123",
    )

    order_fields = {
        "user": user,
        "status": "pending",
        "paid": False,
        "payment_authority": "",
        "payment_request_started_at": None,
    }
    order_fields.update(order_data)

    order = OrderFactory(**order_fields)
    original_status = order.status

    client.force_login(user)

    response = client.post(
        reverse("orders:order_cancel", kwargs={"order_id": order.id})
    )

    order.refresh_from_db()

    assert response.status_code == 302
    assert order.status == original_status


@pytest.mark.django_db
def test_get_request_cannot_cancel_order(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="getuser",
        email="getuser@example.com",
        password="test123",
    )

    order = OrderFactory(user=user, status="pending")

    client.force_login(user)

    response = client.get(
        reverse("orders:order_cancel", kwargs={"order_id": order.id})
    )

    order.refresh_from_db()

    assert response.status_code == 405
    assert order.status == "pending"


@pytest.mark.django_db
def test_cancelling_order_does_not_change_product_stock(
    client,
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="stockuser",
        email="stockuser@example.com",
        password="test123",
    )

    product = ProductFactory(stock=10)

    order = OrderFactory(
        user=user,
        status="pending",
        paid=False,
        payment_authority="",
        payment_request_started_at=None,
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        price_at_purchase=product.price,
        quantity=2,
    )

    client.force_login(user)

    response = client.post(
        reverse("orders:order_cancel", kwargs={"order_id": order.id})
    )

    product.refresh_from_db()

    assert response.status_code == 302
    assert product.stock == 10


import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from orders.access import get_accessible_order
from orders.factories import OrderFactory


def make_request(user=None, guest_order_ids=None):
    request = RequestFactory().get("/")
    request.user = user or AnonymousUser()

    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)

    if guest_order_ids is not None:
        request.session["guest_order_ids"] = guest_order_ids

    return request


@pytest.mark.django_db
def test_guest_can_access_order_from_session():
    order = OrderFactory(user=None)
    request = make_request(guest_order_ids=[order.id])

    result = get_accessible_order(request, order.id)

    assert result == order


@pytest.mark.django_db
def test_guest_cannot_access_order_without_session_permission():
    order = OrderFactory(user=None)
    request = make_request()

    with pytest.raises(Http404):
        get_accessible_order(request, order.id)


@pytest.mark.django_db
def test_owner_can_access_own_order():
    User = get_user_model()
    user = User.objects.create_user(
        username="owner",
        email="owner@example.com",
        password="testpassword123",
    )
    order = OrderFactory(user=user)
    request = make_request(user=user)

    result = get_accessible_order(request, order.id)

    assert result == order


@pytest.mark.django_db
def test_other_user_cannot_access_order():
    User = get_user_model()
    owner = User.objects.create_user(
        username="owner",
        email="owner@example.com",
        password="testpassword123",
    )
    other_user = User.objects.create_user(
        username="other",
        email="other@example.com",
        password="testpassword123",
    )
    order = OrderFactory(user=owner)
    request = make_request(user=other_user)

    with pytest.raises(Http404):
        get_accessible_order(request, order.id)


@pytest.mark.django_db
def test_logged_in_user_can_access_guest_order_from_session():
    User = get_user_model()
    user = User.objects.create_user(
        username="logged_user",
        email="owner@example.com",
        password="testpassword123",
    )
    order = OrderFactory(user=None)
    request = make_request(
        user=user,
        guest_order_ids=[order.id],
    )

    result = get_accessible_order(request, order.id)

    assert result == order

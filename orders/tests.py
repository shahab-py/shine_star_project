from django.test import TestCase
import pytest
from decimal import Decimal
from .factories import OrderFactory, OrderItemFactory
from shop.factories import ProductFactory
from unittest.mock import patch, MagicMock
from django.urls import reverse
from .models import Order

@pytest.mark.django_db
def test_order_total_cost_calculation():
    order = OrderFactory()
    p1 = ProductFactory(price=100000)
    OrderItemFactory(order=order, product=p1, price_at_purchase=100000, quantity=2)
    
    p2 = ProductFactory(price=50000)
    OrderItemFactory(order=order, product=p2, price_at_purchase=50000, quantity=1)
    
    expected_total = Decimal('250000')
    
    assert order.get_total_cost == expected_total

@pytest.mark.django_db
def test_order_item_string_representation():
    product = ProductFactory(name="Lipstick")
    order = OrderFactory()
    item = OrderItemFactory(order=order, product=product, quantity=3)
    
    assert str(item) == "3 x Lipstick"

@pytest.mark.django_db
def test_order_status_choices():
    order = OrderFactory(status='paid')
    assert order.status == 'paid'
    assert order.get_status_display() == 'پرداخت شده'


# VIEWS TESTS

@pytest.mark.django_db
@patch('requests.post')
def test_payment_start_redirects_to_zarinpal(mock_post, client):
    order = OrderFactory()
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'data': {
            'code': 100,
            'authority': 'test_authority_123',
            'url': 'https://www.zarinpal.com/pg/StartPay/test_authority_123'
        }
    }
    mock_post.return_value = mock_response

    url = reverse('orders:payment_start', args=[order.id])
    response = client.get(url)

    assert response.status_code == 302
    assert 'zarinpal.com' in response.url

@pytest.mark.django_db
@patch('requests.post')
def test_payment_verify_success(mock_post, client):
    order = OrderFactory(paid=False)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        'data': {'code': 100}
    }
    mock_post.return_value = mock_response

    url = reverse('orders:payment_verify', args=[order.id])
    response = client.get(url, {'Authority': 'fake_authority'})

    order.refresh_from_db()
    assert order.paid is True
    assert response.status_code == 302
    assert response.url == reverse('orders:order_success')

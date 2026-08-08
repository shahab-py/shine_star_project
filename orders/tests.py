import pytest
from django.conf import settings
from unittest.mock import patch, MagicMock
from django.urls import reverse
from .factories import OrderFactory

@pytest.mark.django_db
@patch('requests.post')
def test_payment_start_redirects_to_zarinpal(mock_post, client, monkeypatch):

    monkeypatch.setattr(settings, 'ZARINPAL', {
        'MERCHANT_ID': 'test_id',
        'START_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/start.json',
    })

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
def test_payment_verify_success(mock_post, client, monkeypatch):
    # ۱. تزریق تنظیمات
    monkeypatch.setattr(settings, 'ZARINPAL', {
        'MERCHANT_ID': 'test_id',
        'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
    })

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

@pytest.mark.django_db
@patch('requests.post')
def test_payment_verify_failure(mock_post, client, monkeypatch):

    monkeypatch.setattr(settings, 'ZARINPAL', {
        'MERCHANT_ID': 'test_id',
        'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
    })

    order = OrderFactory(paid=False)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        'errors': {'message': 'تراکنش ناموفق بود'}
    }
    mock_post.return_value = mock_response

    url = reverse('orders:payment_verify', args=[order.id])
    response = client.get(url, {'Authority': 'fake_authority'})

    order.refresh_from_db()
    assert order.paid is False
    assert 'cart' in response.url

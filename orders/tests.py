import pytest
from django.conf import settings
from unittest.mock import patch, MagicMock
from django.urls import reverse
from .factories import OrderFactory, ProductFactory
from orders.models import Order, OrderItem
from orders.views import payment_verify

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

@pytest.mark.django_db
class TestPaymentWorkflow:

    @patch('orders.views.requests.post')  # شبیه‌سازی درخواست به زرین‌پال
    def test_successful_payment_decreases_stock(self, mock_post, client):
        """
        تست سناریوی موفق: 
        پرداخت تایید می‌شود -> موجودی کالا کم می‌شود -> وضعیت سفارش تغییر می‌کند.
        """
        product = ProductFactory(name="Test Product", stock=10)
        order = Order.objects.create(
            first_name="Test", 
            last_name="User", 
            email="test@test.com",
            address="Street 1",
            city="Tehran",
            postcode="1234567890",
            phone_number="09123456789"
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            price_at_purchase=1000,
            quantity=3
        )
        order.total_price = 3000
        order.save()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'code': 100,
                'message': 'Success'
            }
        }
        mock_post.return_value = mock_response

        url = reverse('orders:payment_verify', args=[order.id])
        client.get(f"{url}?Authority=fake_authority_123")

        # ۴. بررسی نتایج (Assertions)
        order.refresh_from_db()
        product.refresh_from_db()

        assert order.paid is True, "سفارش نباید پرداخت نشده باقی بماند"
        assert order.status == 'paid', "وضعیت سفارش نباید تغییر نکند"
        assert product.stock == 7, f"موجودی نباید تغییر نکند. انتظار ۷ داشتیم، اما {product.stock} شد"

    @patch('orders.views.requests.post')
    def test_failed_payment_does_not_decrease_stock(self, mock_post, client):
        """
        تست سناریوی شکست:
        پرداخت ناموفق است -> موجودی نباید کم شود -> وضعیت سفارش نباید تغییر کند.
        """

        product = ProductFactory(name="Failed Product", stock=10)
        order = Order.objects.create(
            first_name="Test", last_name="User", email="t@t.com",
            address="A", city="B", postcode="1", phone_number="1"
        )
        OrderItem.objects.create(order=order, product=product, price_at_purchase=100, quantity=2)
        order.total_price = 200
        order.save()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'code': 401, 'message': 'Invalid Authority'},
            'errors': [{'message': 'پرداخت ناموفق بود'}]
        }
        mock_post.return_value = mock_response

        url = reverse('orders:payment_verify', args=[order.id])
        client.get(f"{url}?Authority=wrong_authority")

        order.refresh_from_db()
        product.refresh_from_db()

        assert order.paid is False, "در صورت شکست پرداخت، سفارش نباید Paid شود"
        assert product.stock == 10, "در صورت شکست پرداخت، موجودی نباید کم شود"


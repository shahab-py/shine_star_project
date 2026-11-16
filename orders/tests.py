import pytest
import requests
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
    client.force_login(order.user)
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
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
    order.refresh_from_db()
    assert order.payment_authority == 'test_authority_123'
    assert order.payment_request_started_at is None


@pytest.mark.django_db
@patch('orders.views.requests.post')
def test_payment_start_timeout_keeps_request_reserved(
    mock_post, client, monkeypatch
):
    monkeypatch.setattr(settings, 'ZARINPAL', {
        'MERCHANT_ID': 'test_id',
        'START_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
    })

    order = OrderFactory()
    client.force_login(order.user)

    mock_post.side_effect = requests.Timeout(
        "Connection timed out"
    )

    url = reverse('orders:payment_start', args=[order.id])
    response = client.get(url)

    order.refresh_from_db()

    assert response.status_code == 302
    assert order.payment_request_started_at is not None
    assert order.payment_authority == ""
    mock_post.assert_called_once()

    # درخواست مجدد نباید به درگاه ارسال شود.
    response = client.get(url)

    assert response.status_code == 302
    mock_post.assert_called_once()

@pytest.mark.django_db
@patch('orders.views.requests.post')
def test_payment_start_explicit_rejection_releases_reservation(
    mock_post, client, monkeypatch
):
    monkeypatch.setattr(settings, 'ZARINPAL', {
        'MERCHANT_ID': 'test_id',
        'START_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
    })

    order = OrderFactory()
    client.force_login(order.user)

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'data': {
            'code': -9,
        },
        'errors': {
            'code': -9,
            'message': 'Invalid request',
        },
    }
    mock_post.return_value = mock_response

    url = reverse('orders:payment_start', args=[order.id])
    response = client.get(url)

    order.refresh_from_db()

    assert response.status_code == 302
    assert order.payment_request_started_at is None
    assert order.payment_authority == ''
    mock_post.assert_called_once()


@pytest.mark.django_db
@patch('orders.views.requests.post')
def test_payment_start_missing_authority_keeps_request_reserved(
    mock_post, client, monkeypatch
):
    monkeypatch.setattr(settings, 'ZARINPAL', {
        'MERCHANT_ID': 'test_id',
        'START_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
    })

    order = OrderFactory()
    client.force_login(order.user)

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'data': {
            'code': 100,
            'authority': '',
        }
    }
    mock_post.return_value = mock_response

    url = reverse('orders:payment_start', args=[order.id])
    response = client.get(url)

    order.refresh_from_db()

    assert response.status_code == 302
    assert order.payment_request_started_at is not None
    assert order.payment_authority == ''
    mock_post.assert_called_once()

@pytest.mark.django_db
@patch('orders.views.requests.post')
def test_payment_verify_success(mock_post, client, monkeypatch):
    monkeypatch.setattr(settings, 'ZARINPAL', {
        'MERCHANT_ID': 'test_id',
        'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
    })

    order = OrderFactory(
        paid=False,
        payment_authority='fake_authority',
    )

    product = ProductFactory(stock=10)

    OrderItem.objects.create(
        order=order,
        product=product,
        price_at_purchase=100,
        quantity=1,
)

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'data': {
            'code': 100,
            'ref_id': 123456789,
        }
    }
    mock_post.return_value = mock_response

    url = reverse('orders:payment_verify', args=[order.id])
    response = client.get(
        url,
        {
            'Authority': 'fake_authority',
            'Status': 'OK',
        },
    )

    order.refresh_from_db()

    assert order.paid is True
    assert order.status == 'paid'
    assert order.payment_ref_id == '123456789'
    assert response.status_code == 302
    assert response.url == reverse(
        'orders:order_success',
        kwargs={'order_id': order.id},
    )
    mock_post.assert_called_once()


@pytest.mark.django_db
@patch('orders.views.requests.post')
def test_payment_verify_failure(mock_post, client, monkeypatch):
    monkeypatch.setattr(settings, 'ZARINPAL', {
        'MERCHANT_ID': 'test_id',
        'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
    })

    order = OrderFactory(
        paid=False,
        payment_authority='fake_authority',
    )

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'errors': {
            'message': 'تراکنش ناموفق بود',
        }
    }
    mock_post.return_value = mock_response

    url = reverse('orders:payment_verify', args=[order.id])
    response = client.get(
        url,
        {
            'Authority': 'fake_authority',
            'Status': 'OK',
        },
    )

    order.refresh_from_db()

    assert order.paid is False
    assert order.status == 'pending'
    assert response.url == reverse('shop:product_list')
    mock_post.assert_called_once()

@pytest.mark.django_db
@patch('orders.views.requests.post')
def test_paid_order_rejects_wrong_authority(
    mock_post, client
):
    order = OrderFactory(
        paid=True,
        status="paid",
        payment_authority="correct_authority",
    )

    url = reverse(
        "orders:payment_verify",
        args=[order.id],
    )

    response = client.get(url, {
        "Authority": "wrong_authority",
        "Status": "OK",
    })

    assert response.status_code == 302
    assert response.url == reverse("shop:product_list")
    mock_post.assert_not_called()

@pytest.mark.django_db
@patch('orders.views.requests.post')
def test_payment_verify_accepts_code_101(
    mock_post, client, monkeypatch
):
    monkeypatch.setattr(settings, 'ZARINPAL', {
        'MERCHANT_ID': 'test_id',
        'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
    })

    product = ProductFactory(stock=10)

    order = OrderFactory(
        paid=False,
        status="pending",
        payment_authority="authority_101",
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        price_at_purchase=100,
        quantity=2,
    )

    order.total_price = 100
    order.save(update_fields=["total_price"])

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "data": {
            "code": 101,
            "ref_id": 987654321,
        }
    }
    mock_post.return_value = mock_response

    url = reverse(
        "orders:payment_verify",
        args=[order.id],
    )

    response = client.get(url, {
        "Authority": "authority_101",
        "Status": "OK",
    })

    order.refresh_from_db()
    product.refresh_from_db()

    assert response.status_code == 302
    assert order.paid is True
    assert order.status == "paid"
    assert order.payment_ref_id == "987654321"
    assert product.stock == 8

@pytest.mark.django_db
class TestPaymentWorkflow:


    @patch('orders.views.requests.post')
    def test_successful_payment_decreases_stock(
        self, mock_post, client, monkeypatch
    ):
        monkeypatch.setattr(settings, 'ZARINPAL', {
            'MERCHANT_ID': 'test_id',
            'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
        })

        product = ProductFactory(name="Test Product", stock=10)

        order = Order.objects.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            address="Street 1",
            city="Tehran",
            postcode="1234567890",
            phone_number="09123456789",
            payment_authority="fake_authority_123",
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price_at_purchase=1000,
            quantity=3,
        )

        order.total_price = 3000
        order.save()

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'data': {
                'code': 100,
                'ref_id': 987654321,
            }
        }
        mock_post.return_value = mock_response

        url = reverse('orders:payment_verify', args=[order.id])

        response = client.get(
            url,
            {
                'Authority': 'fake_authority_123',
                'Status': 'OK',
            },
        )

        order.refresh_from_db()
        product.refresh_from_db()

        assert response.status_code == 302
        assert order.paid is True
        assert order.status == 'paid'
        assert order.payment_ref_id == '987654321'
        assert product.stock == 7
        mock_post.assert_called_once()


    @patch('orders.views.requests.post')
    def test_duplicate_callback_does_not_decrease_stock_again(
        self, mock_post, client, monkeypatch
    ):
        monkeypatch.setattr(settings, 'ZARINPAL', {
            'MERCHANT_ID': 'test_id',
            'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
        })

        product = ProductFactory(name="Duplicate Test Product", stock=10)

        order = Order.objects.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            address="Street 1",
            city="Tehran",
            postcode="1234567890",
            phone_number="09123456789",
            payment_authority="duplicate_authority",
            total_price=3000,
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price_at_purchase=1000,
            quantity=3,
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'data': {
                'code': 100,
                'ref_id': 987654321,
            }
        }
        mock_post.return_value = mock_response

        url = reverse('orders:payment_verify', args=[order.id])
        callback_data = {
            'Authority': 'duplicate_authority',
            'Status': 'OK',
        }

        client.get(url, callback_data)
        client.get(url, callback_data)

        order.refresh_from_db()
        product.refresh_from_db()

        assert order.paid is True
        assert product.stock == 7
        mock_post.assert_called_once()


    @patch('orders.views.requests.post')
    def test_failed_payment_does_not_decrease_stock(
        self, mock_post, client, monkeypatch
    ):
        monkeypatch.setattr(settings, 'ZARINPAL', {
            'MERCHANT_ID': 'test_id',
            'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
        })
        product = ProductFactory(name="Failed Product", stock=10)
        order = Order.objects.create(
            first_name="Test",
            last_name="User",
            email="t@t.com",
            address="A",
            city="B",
            postcode="1",
            phone_number="1",
            payment_authority="test_authority",
        )

        OrderItem.objects.create(order=order, product=product, price_at_purchase=100, quantity=2)
        order.total_price = 200
        order.save()

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'data': {
                'code': 401,
                'message': 'Invalid Authority',
            },
            'errors': [
                {'message': 'پرداخت ناموفق بود'}
            ],
        }
        mock_post.return_value = mock_response

        url = reverse('orders:payment_verify', args=[order.id])

        client.get(url, {
            'Authority': 'test_authority',
            'Status': 'OK',
        })

        order.refresh_from_db()
        product.refresh_from_db()

        assert order.paid is False
        assert order.status == "pending"
        assert product.stock == 10

        mock_post.assert_called_once()


    @pytest.mark.django_db
    @patch('orders.views.requests.post')
    def test_insufficient_stock_marks_order_for_review(
        self, mock_post, client, monkeypatch
    ):
        monkeypatch.setattr(settings, 'ZARINPAL', {
            'MERCHANT_ID': 'test_id',
            'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
        })

        product_1 = ProductFactory(
            name="Product One",
            stock=10,
        )

        product_2 = ProductFactory(
            name="Product Two",
            stock=1,
        )

        order = Order.objects.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            address="Street 1",
            city="Tehran",
            postcode="1234567890",
            phone_number="09123456789",
            payment_authority="test_authority",
            total_price=500,
        )

        OrderItem.objects.create(
            order=order,
            product=product_1,
            price_at_purchase=100,
            quantity=3,
        )

        OrderItem.objects.create(
            order=order,
            product=product_2,
            price_at_purchase=200,
            quantity=2,
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'data': {
                'code': 100,
                'ref_id': 123456789,
            }
        }
        mock_post.return_value = mock_response

        url = reverse('orders:payment_verify', args=[order.id])

        client.get(url, {
            'Authority': 'test_authority',
            'Status': 'OK',
        })

        order.refresh_from_db()
        product_1.refresh_from_db()
        product_2.refresh_from_db()

        assert order.paid is True
        assert order.status == "payment_review"
        assert order.payment_ref_id == "123456789"
        assert product_1.stock == 10
        assert product_2.stock == 1

        mock_post.assert_called_once()

    @patch('orders.views.requests.post')
    def test_expired_order_can_be_paid_after_valid_callback(
        self, mock_post, client, monkeypatch
    ):
        from django.utils import timezone
        from datetime import timedelta

        monkeypatch.setattr(settings, 'ZARINPAL', {
            'MERCHANT_ID': 'test_id',
            'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
        })

        product = ProductFactory(stock=10)

        order = Order.objects.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            address="Street 1",
            city="Tehran",
            postcode="1234567890",
            phone_number="09123456789",
            payment_authority="expired_authority",
            status="expired",
            expires_at=timezone.now() - timedelta(minutes=10),
            total_price=200,
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price_at_purchase=100,
            quantity=2,
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'data': {
                'code': 100,
                'ref_id': 123456789,
            }
        }
        mock_post.return_value = mock_response

        url = reverse('orders:payment_verify', args=[order.id])

        response = client.get(url, {
            'Authority': 'expired_authority',
            'Status': 'OK',
        })

        order.refresh_from_db()
        product.refresh_from_db()

        assert response.status_code == 302
        assert order.paid is True
        assert order.status == "paid"
        assert order.payment_ref_id == "123456789"
        assert product.stock == 8
        mock_post.assert_called_once()


    @patch('orders.views.requests.post')
    def test_duplicate_callback_does_not_process_payment_review_again(
        self, mock_post, client, monkeypatch
    ):
        monkeypatch.setattr(settings, 'ZARINPAL', {
            'MERCHANT_ID': 'test_id',
            'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
        })

        product = ProductFactory(stock=1)

        order = Order.objects.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            address="Street 1",
            city="Tehran",
            postcode="1234567890",
            phone_number="09123456789",
            payment_authority="review_authority",
            status="payment_review",
            paid=True,
            payment_ref_id="987654321",
            total_price=200,
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price_at_purchase=100,
            quantity=2,
        )

        url = reverse('orders:payment_verify', args=[order.id])

        callback_data = {
            'Authority': 'review_authority',
            'Status': 'OK',
        }

        response_1 = client.get(url, callback_data)
        response_2 = client.get(url, callback_data)

        order.refresh_from_db()
        product.refresh_from_db()

        assert response_1.status_code == 302
        assert response_2.status_code == 302
        assert order.paid is True
        assert order.status == "payment_review"
        assert order.payment_ref_id == "987654321"
        assert product.stock == 1
        mock_post.assert_not_called()

    @patch('orders.views.requests.post')
    def test_missing_ref_id_does_not_mark_order_as_paid(
        self, mock_post, client, monkeypatch
    ):
        monkeypatch.setattr(settings, 'ZARINPAL', {
            'MERCHANT_ID': 'test_id',
            'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
        })

        product = ProductFactory(
            name="Missing Ref Product",
            stock=10,
        )

        order = Order.objects.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            address="Street 1",
            city="Tehran",
            postcode="1234567890",
            phone_number="09123456789",
            payment_authority="missing_ref_authority",
            total_price=200,
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price_at_purchase=100,
            quantity=2,
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'data': {
                'code': 100,
            }
        }
        mock_post.return_value = mock_response

        url = reverse('orders:payment_verify', args=[order.id])

        client.get(url, {
            'Authority': 'missing_ref_authority',
            'Status': 'OK',
        })

        order.refresh_from_db()
        product.refresh_from_db()

        assert order.paid is False
        assert order.status == "pending"
        assert order.payment_ref_id == ""
        assert product.stock == 10

        mock_post.assert_called_once()
    @patch('orders.views.requests.post')
    def test_empty_order_is_not_marked_as_paid(
        self, mock_post, client, monkeypatch
    ):
        monkeypatch.setattr(settings, 'ZARINPAL', {
            'MERCHANT_ID': 'test_id',
            'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
        })

        order = OrderFactory(
            paid=False,
            status="pending",
            payment_authority="empty_order_authority",
            total_price=0,
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'data': {
                'code': 100,
                'ref_id': 123456789,
            }
        }
        mock_post.return_value = mock_response

        url = reverse('orders:payment_verify', args=[order.id])

        response = client.get(url, {
            'Authority': 'empty_order_authority',
            'Status': 'OK',
        })

        order.refresh_from_db()

        assert response.status_code == 302
        assert order.paid is False
        assert order.status == "pending"
        assert order.payment_ref_id == ""
        mock_post.assert_called_once()

@pytest.mark.django_db
@patch('orders.views.requests.post')
def test_payment_verify_nok_does_not_call_gateway(
    mock_post, client
):
    product = ProductFactory(
        name="NOK Test Product",
        stock=10,
    )

    order = Order.objects.create(
        first_name="Test",
        last_name="User",
        email="test@test.com",
        address="Street 1",
        city="Tehran",
        postcode="1234567890",
        phone_number="09123456789",
        payment_authority="test_authority",
        total_price=200,
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        price_at_purchase=100,
        quantity=2,
    )

    url = reverse(
        'orders:payment_verify',
        args=[order.id],
    )

    response = client.get(url, {
        'Authority': 'test_authority',
        'Status': 'NOK',
    })

    order.refresh_from_db()
    product.refresh_from_db()

    assert response.status_code == 302
    assert order.paid is False
    assert order.status == "pending"
    assert product.stock == 10

    mock_post.assert_not_called()

@pytest.mark.django_db
def test_api_create_order_success(client):
    product = ProductFactory(
        price=100000,
        stock=10,
        is_available=True,
    )

    # آماده‌سازی نشست کاربر
    session = client.session
    session['cart'] = {
        str(product.id): {
            'quantity': 2,
            'price': str(product.price),
        }
    }
    session.save()

    url = reverse('orders:order_create_api')

    response = client.post(
        url,
        data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'address': 'Test Address',
            'city': 'Tehran',
            'postcode': '1234567890',
            'phone_number': '09123456789',
        },
        content_type='application/json',
    )

    assert response.status_code == 201
    assert Order.objects.count() == 1

    order = Order.objects.first()

    assert order.total_price == 200000
    assert order.status == 'pending'
    assert order.items.count() == 1

    order_item = order.items.first()

    assert order_item.product == product
    assert order_item.quantity == 2
    assert order_item.price_at_purchase == 100000

    product.refresh_from_db()
    assert product.stock == 10

@pytest.mark.django_db
def test_api_create_order_with_empty_cart(client):
    url = reverse('orders:order_create_api')

    response = client.post(
        url,
        data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'address': 'Test Address',
            'city': 'Tehran',
            'postcode': '1234567890',
            'phone_number': '09123456789',
        },
        content_type='application/json',
    )

    assert response.status_code == 400
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_api_create_order_ignores_cart_price(client):
    product = ProductFactory(
        price=100000,
        stock=10,
        is_available=True,
    )

    session = client.session
    session['cart'] = {
        str(product.id): {
            'quantity': 2,
            'price': '1',
        }
    }
    session.save()

    url = reverse('orders:order_create_api')

    response = client.post(
        url,
        data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'address': 'Test Address',
            'city': 'Tehran',
            'postcode': '1234567890',
            'phone_number': '09123456789',
        },
        content_type='application/json',
    )

    assert response.status_code == 201

    order = Order.objects.get()

    assert order.total_price == 200000
    assert order.items.first().price_at_purchase == 100000
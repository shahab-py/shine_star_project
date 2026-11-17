
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from orders.models import Order


@pytest.mark.django_db
class TestExpireOrdersCommand:

    def create_order(self, **kwargs):
        data = {
            "first_name": "Test",
            "last_name": "Expiry",
            "email": "test@example.com",
            "address": "Test Address",
            "city": "Test City",
            "postcode": "0000000000",
            "phone_number": "00000000000",
            "status": "pending",
            "paid": False,
            "expires_at": timezone.now() - timedelta(minutes=5),
        }
        data.update(kwargs)
        return Order.objects.create(**data)

    def test_expires_eligible_order(self):
        order = self.create_order()

        call_command("expire_orders")

        order.refresh_from_db()
        assert order.status == "expired"
        assert order.paid is False

    def test_does_not_expire_order_with_payment_request(self):
        order = self.create_order(
            payment_request_started_at=timezone.now()
        )

        call_command("expire_orders")

        order.refresh_from_db()
        assert order.status == "pending"

    def test_does_not_expire_order_with_authority(self):
        order = self.create_order(
            payment_authority="test-authority"
        )

        call_command("expire_orders")

        order.refresh_from_db()
        assert order.status == "pending"

    def test_does_not_expire_order_before_deadline(self):
        order = self.create_order(
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        call_command("expire_orders")

        order.refresh_from_db()
        assert order.status == "pending"

    def test_does_not_expire_paid_order(self):
        order = self.create_order(paid=True)

        call_command("expire_orders")

        order.refresh_from_db()
        assert order.status == "pending"

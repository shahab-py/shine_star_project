
from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Order


class Command(BaseCommand):
    help = "Expire eligible pending orders"

    def handle(self, *args, **options):
        now = timezone.now()

        expired_count = Order.objects.filter(
            status="pending",
            expires_at__lte=now,
            payment_request_started_at__isnull=True,
            payment_authority="",
            paid=False,
        ).update(status="expired")

        self.stdout.write(
            self.style.SUCCESS(
                f"{expired_count} order(s) expired successfully."
            )
        )

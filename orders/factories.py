import factory
from django.contrib.auth import get_user_model

from .models import Order, OrderItem
from shop.factories import ProductFactory


User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = "test-password"


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    first_name = "Test"
    last_name = "User"
    email = "test@example.com"
    address = "123 Test Street"
    city = "Tehran"
    postcode = "1234567890"
    phone_number = "09123456789"
    paid = False
    status = "pending"


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    price_at_purchase = 50000
    quantity = 1

import pytest
from django.core.exceptions import ValidationError
from .factories import ProductFactory, CategoryFactory
from django.urls import reverse
from .models import Product, Category


#MODEOLS TESTS
@pytest.mark.django_db
def test_product_creation_with_factory():
    product = ProductFactory(name="Special Lipstick", price=200000)

    assert product.name == "Special Lipstick"
    assert product.price == 200000
    assert product.category is not None
    assert product.category.name.startswith("Category")

@pytest.mark.django_db
def test_multiple_products_with_different_categories():
    p1 = ProductFactory(name="P1")
    p2 = ProductFactory(name="P2")

    assert p1.category != p2.category

@pytest.mark.django_db
def test_product_negative_price_raises_error():
    category = CategoryFactory()
    
    product = ProductFactory.build(price=-100, category=category)
    
    with pytest.raises(ValidationError):
        product.full_clean()

@pytest.mark.django_db
def test_product_negative_stock_raises_error():
    category = CategoryFactory()
    
    product = ProductFactory.build(stock=-5, category=category)

    with pytest.raises(ValidationError):
        product.full_clean()



# VIEWS TESTS
@pytest.mark.django_db
def test_product_list_view(client):
    p1 = ProductFactory(name="Available Product", is_available=True)
    p2 = ProductFactory(name="Unavailable Product", is_available=False)
    
    response = client.get(reverse('shop:product_list'))
    
    assert response.status_code == 200
    assert p1.name in response.content.decode()
    assert p2.name not in response.content.decode()

@pytest.mark.django_db
def test_product_detail_view(client):
    product = ProductFactory(name="Detail Product")
    
    url = reverse('shop:product_detail', args=[product.pk])
    response = client.get(url)
    
    assert response.status_code == 200
    assert product.name in response.content.decode()

@pytest.mark.django_db
def test_cart_add_view(client):
    product = ProductFactory(name="Cart Product")
    
    url = reverse('shop:cart_add', args=[product.id])
    response = client.get(url)
    
    assert response.status_code == 302
    assert response.url == reverse('shop:cart_detail')

@pytest.mark.django_db
def test_cart_remove_view(client):
    product = ProductFactory(name="Remove Product")
    
    client.get(reverse('shop:cart_add', args=[product.id]))
    
    url = reverse('shop:cart_remove', args=[product.id])
    response = client.get(url)
    
    assert response.status_code == 302
    assert response.url == reverse('shop:cart_detail')
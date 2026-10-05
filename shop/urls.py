from django.urls import path
from . import views, views_product, views_cart
from .api_views import ProductListAPIView, ProductDetailAPIView
from .api_cart_views import CartAPIView, CartAddAPIView

app_name = 'shop'

urlpatterns = [

    path('', views.home, name='home'),
    path('api/products/', ProductListAPIView.as_view(), name='product_list_api'),
    path('api/products/<int:pk>/', ProductDetailAPIView.as_view(), name='product_detail_api'),
    path('products/', views_product.product_list, name='product_list'),
    path('product/<int:pk>/', views_product.product_detail, name='product_detail'),
    path('cart/add/<int:product_id>/', views_cart.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views_cart.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views_cart.cart_remove, name='cart_remove'),
    path('cart/', views_cart.cart_detail, name='cart_detail'),
    path('checkout/', views_cart.checkout_view, name='checkout'),
    path('api/cart/', CartAPIView.as_view(), name='cart_api'),
    path('api/cart/add/', CartAddAPIView.as_view(), name='cart_api_add'),
]
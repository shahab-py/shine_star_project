from django.urls import path
from . import views, views_product, views_cart

app_name = 'shop'

urlpatterns = [

    path('', views.home, name='home'),
    path('products/', views_product.product_list, name='product_list'),
    path('product/<int:pk>/', views_product.product_detail, name='product_detail'),
    path('cart/add/<int:product_id>/', views_cart.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views_cart.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views_cart.cart_remove, name='cart_remove'),
    path('cart/', views_cart.cart_detail, name='cart_detail'),
    path('checkout/', views_cart.checkout_view, name='checkout'),
]
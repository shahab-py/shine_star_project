from django.urls import path
from . import views, views_order




app_name = 'orders'

urlpatterns = [
    path('create/', views_order.OrderCreateView.as_view(), name='order_create'),
    path('order/success/', views_order.order_success, name='order_success'),    
    path('create/', views_order.OrderCreateView.as_view(), name='create'),
    path('payment/<int:order_id>/', views.payment_start, name='payment_start'),
    path('payment/verify/<int:order_id>/', views.payment_verify, name='payment_verify'),
]

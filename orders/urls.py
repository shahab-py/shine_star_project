from django.urls import path
from . import views, views_order, api_views
from .api_views import OrderCreateAPIView

app_name = 'orders'

urlpatterns = [

    path('create/', views_order.OrderCreateView.as_view(), name='order_create'),
    path('api/create/', OrderCreateAPIView.as_view(), name='order_create_api'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),    
    path('payment/start/<int:order_id>/', views.payment_start, name='payment_start'),
    path('payment/verify/<int:order_id>/', views.payment_verify, name='payment_verify'),
    path('my-orders/', api_views.OrderListView.as_view(), name='order-list'),
]

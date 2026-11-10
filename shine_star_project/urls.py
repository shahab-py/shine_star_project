
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include(('shop.urls', 'shop'), namespace='shop')),
    path('shop/', include(('shop.urls', 'shop'), namespace='shop_prefixed')),
    path('admin/', admin.site.urls),
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

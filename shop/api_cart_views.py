from rest_framework.views import APIView
from rest_framework.response import Response
from .cart import Cart
from shop.models import Product

class CartAPIView(APIView):
    def get(self, request):
        cart = Cart(request)
        cart_items = []
        for item in cart:
            cart_items.append({
                'product_id': item['product'].id,
                'name': item['product'].name,
                'price': item['price'],
                'quantity': item['quantity'],
                'total_price': item['price'] * item['quantity'],
            })
        
        return Response({
            'items': cart_items,
            'total_price': cart.get_total_price(),
        })



class CartAddAPIView(APIView):
    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        cart = Cart(request)
        product = Product.objects.get(id=product_id)
        cart.add(product=product, quantity=int(quantity))
        return Response({"message": "Product added to cart"})
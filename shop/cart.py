from decimal import Decimal
from .models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    @property
    def items(self):
        """
        این همان قطعه گمشده است! 
        با این کار، وقتی در views می‌گویی cart.items، 
        دقیقاً مقادیر داخل سبد خرید را برمی‌گرداند.
        """
        return self.cart.values()

    def add(self, product, quantity=None, override_quantity=None):
        """اضافه کردن محصول یا تغییر مقدار آن"""
        product_id = str(product.id)
        
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0, 
                'price': str(product.price)
            }
        
        if override_quantity:
            self.cart[product_id]['quantity'] = override_quantity
        else:
            self.cart[product_id]['quantity'] += quantity or 1
        
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        
        cart_data = {}
        
        for product in products:
            p_id = str(product.id)
            if p_id in self.cart:
                price_val = self.cart[p_id].get('price', '0')
                quantity_val = self.cart[p_id].get('quantity', 0)
                
                cart_data[p_id] = {
                    'product': product,
                    'price': Decimal(str(price_val)),
                    'quantity': quantity_val
                }
        
        for item in cart_data.values():
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        total = Decimal(0)
        for item in self.cart.values():
            price = Decimal(item.get('price', 0))
            quantity = item.get('quantity', 0)
            total += price * quantity
        return total

    def clear(self):
        if 'cart' in self.session:
            del self.session['cart']
        self.save()

from decimal import Decimal
from django.conf import settings
from .models import Product


class Cart:
    def __init__(self, request):
        """Инициализируем корзину на основе сессии."""
        self.session = request.session
        cart = self.session.get('cart')

        if not cart:
            # Если корзина ещё не создана, создаём пустую
            cart = self.session['cart'] = {}

        self.cart = cart

    def add(self, product, quantity=1):
        """Добавляем товар в корзину или обновляем его количество."""
        product_id = str(product.id)

        if product_id in self.cart:
            self.cart[product_id]['quantity'] += quantity
        else:
            self.cart[product_id] = {
                'quantity': quantity,
                'price': str(product.price)
            }

        # Сохраняем корзину в сессию
        self.save()

    def get_items(self):
        """Получаем все товары в корзине."""
        items = []
        for product_id, data in self.cart.items():
            product = Product.objects.get(id=product_id)
            total_price = Decimal(data['price']) * data['quantity']
            items.append({
                'product': product,
                'quantity': data['quantity'],
                'total_price': total_price
            })
        return items

    def get_total_price(self):
        """Вычисляем общую стоимость корзины."""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def remove(self, product):
        """Удаляем товар из корзины."""
        product_id = str(product.id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        """Сохраняем корзину в сессию."""
        self.session['cart'] = self.cart
        self.session.modified = True

    def clear(self):
        """Очищаем корзину."""
        del self.session['cart']
        self.session.modified = True

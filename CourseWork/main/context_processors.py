from .cart import Cart


def cart_items_count(request):
    """Добавляет количество товаров в корзине в шаблоны."""
    cart = Cart(request)
    return {'cart_items_count': len(cart.cart)}

from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .cart import Cart  # Создадим класс Cart для обработки корзины
from .forms import OrderForm  # Создадим форму для оформления заказа


def home(request):
    category_slug = request.GET.get("category")  # Получаем параметр из URL (например, ?category=pizza)

    categories = ProductCategory.objects.all()  # Все категории
    products = Product.objects.all()  # Все товары

    if category_slug:
        selected_category = ProductCategory.objects.filter(slug=category_slug).first()
        if selected_category:
            products = products.filter(category=selected_category)  # Фильтруем товары по категории

    context = {
        "categories": categories,
        "products": products,
        "selected_category": category_slug,
    }

    return render(request, "index.html", context=context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    context = {
        "product": product,
    }

    return render(request, 'product_detail.html', context=context)


def cart(request):
    cart = Cart(request)

    context = {
        'cart_items': cart.get_items(),
        'total_price': cart.get_total_price()
    }

    return render(request, 'cart.html', context=context)


def checkout(request):
    cart = Cart(request)

    if request.method == 'POST':
        form = OrderForm(request.POST, user=request.user)  # Передаём пользователя в форму
        if form.is_valid():
            order = form.save()
            cart.clear()  # Очищаем корзину после успешного заказа
            return redirect('orders')  # Редирект на страницу с заказами
    else:
        form = OrderForm(user=request.user)  # Передаём пользователя в форму

    context = {
        'cart_items': cart.get_items(),
        'total_price': cart.get_total_price(),
        'form': form
    }

    return render(request, 'checkout.html', context=context)


def orders(request):
    orders = Order.objects.filter(user=request.user)  # Предполагаем, что у пользователя есть авторизация

    context = {
        'orders': orders
    }

    return render(request, 'orders.html', context=context)


def cart_add(request, product_id):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)

    if request.method == 'POST':
        cart.add(product=product, quantity=1)

    return redirect('cart')


def cart_remove(request, product_id):
    """Удаляет товар из корзины"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.remove(product)  # Удаляем товар из корзины
    return redirect('cart')  # Перенаправляем обратно в корзину
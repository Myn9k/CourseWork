from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .cart import Cart  # Создадим класс Cart для обработки корзины
from .forms import OrderForm  # Создадим форму для оформления заказа
import uuid


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
    cart = Cart(request)  # Создаём объект корзины
    guest_id = get_guest_id(request)  # Получаем `guest_id` из куки

    if request.method == 'POST':
        if request.user.is_authenticated:
            # Авторизованный пользователь
            order = Order.objects.create(user=request.user, total_price=cart.get_total_price())
        else:
            # Анонимный пользователь
            full_name = request.POST.get("full_name")
            phone = request.POST.get("phone")
            email = request.POST.get("email")

            if not full_name or not phone or not email:
                return render(request, 'checkout.html', {
                    'cart_items': cart.get_items(),  # Ошибка была тут!
                    'total_price': cart.get_total_price(),
                    'error': 'Для оформления заказа заполните все поля.'
                })

            order = Order.objects.create(
                full_name=full_name,
                phone=phone,
                email=email,
                guest_id=guest_id,
                total_price=cart.get_total_price()
            )

        for item in cart.get_items():
            OrderItem.objects.create(order=order, product=item['product'], quantity=item['quantity'])

        cart.clear()  # Очищаем корзину после оформления заказа

        response = redirect('orders')
        if not request.user.is_authenticated:
            response.set_cookie('guest_id', guest_id, max_age=60*60*24*30)  # Сохраняем `guest_id` на 30 дней
        return response

    context = {
        'cart_items': cart.get_items(),
        'total_price': cart.get_total_price(),
    }

    return render(request, 'checkout.html', context=context)


def orders(request):
    """Показываем заказы авторизованного или анонимного пользователя"""
    guest_id = get_guest_id(request)

    if request.user.is_authenticated:
        user_orders = Order.objects.filter(user=request.user)  # Авторизованный пользователь
    else:
        user_orders = Order.objects.filter(guest_id=guest_id)  # Анонимный пользователь

    context = {
        'orders': user_orders
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


def get_guest_id(request):
    """Получает или создаёт уникальный идентификатор для анонимного пользователя."""
    guest_id = request.COOKIES.get('guest_id')
    if not guest_id:
        guest_id = str(uuid.uuid4())  # Генерируем случайный ID
    return guest_id
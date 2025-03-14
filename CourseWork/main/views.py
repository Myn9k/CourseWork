from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .cart import Cart  # Создадим класс Cart для обработки корзины
from .forms import OrderForm  # Создадим форму для оформления заказа
import uuid
from django.contrib.auth.decorators import login_required


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
    cart = Cart(request)  # Получаем корзину
    guest_id = get_guest_id(request)  # Получаем `guest_id` из cookies

    if request.method == 'POST':
        # Проверяем, есть ли адрес в POST-запросе, иначе оставляем пустую строку
        address_text = request.POST.get("address", "").strip()

        if request.user.is_authenticated:
            # Проверяем, есть ли этот адрес у пользователя
            address, created = UserAddress.objects.get_or_create(
                user=request.user, address=address_text
            )

            # Создаём заказ с привязкой к адресу
            order = Order.objects.create(
                user=request.user,
                total_price=cart.get_total_price(),
                address=address  # Сохраняем `UserAddress`
            )
        else:
            # Данные гостя
            full_name = request.POST.get("full_name", "").strip()
            phone = request.POST.get("phone", "").strip()
            email = request.POST.get("email", "").strip()

            if not all([full_name, phone, email, address_text]):
                return render(request, 'checkout.html', {
                    'cart_items': cart.get_items(),
                    'total_price': cart.get_total_price(),
                    'error': 'Все поля обязательны!',
                })

            # Создаём заказ для гостя (сохранение адреса в `guest_address`)
            order = Order.objects.create(
                full_name=full_name,
                phone=phone,
                email=email,
                guest_id=guest_id,
                total_price=cart.get_total_price(),
                guest_address=address_text  # Теперь адрес хранится правильно!
            )

        # Сохраняем товары и кастомизацию
        for item in cart.get_items():
            order_item = OrderItem.objects.create(order=order, product=item['product'], quantity=item['quantity'])

            for key, value in request.POST.items():
                if key.startswith(f"customization_{item['product'].id}_"):
                    ingredient_id = key.split("_")[-1]
                    action = value  # "add" или "remove"
                    ingredient = Ingredient.objects.get(id=ingredient_id)

                    # Получаем `ProductIngredient`, чтобы взять `remove_price`
                    product_ingredient = ProductIngredient.objects.filter(
                        product=item['product'], ingredient=ingredient
                    ).first()

                    # Если действие "remove", берём `remove_price` из `ProductIngredient`
                    remove_price = product_ingredient.remove_price if product_ingredient else 0

                    OrderItemCustomization.objects.create(
                        order_item=order_item,
                        ingredient=ingredient,
                        action=action,
                        price=ingredient.base_price if action == "add" else remove_price
                    )

        cart.clear()  # Очищаем корзину после оформления заказа

        response = redirect('orders')
        if not request.user.is_authenticated:
            response.set_cookie('guest_id', guest_id, max_age=60 * 60 * 24 * 30)  # Запоминаем `guest_id` на 30 дней
        return response

    context = {
        'cart_items': cart.get_items(),
        'total_price': cart.get_total_price(),
    }

    return render(request, 'checkout.html', context=context)



def orders_list(request):
    """Показываем заказы авторизованного или анонимного пользователя"""
    guest_id = get_guest_id(request)

    if request.user.is_authenticated:
        user_orders = Order.objects.filter(user=request.user)  # Авторизованный пользователь
    else:
        user_orders = Order.objects.filter(guest_id=guest_id)  # Анонимный пользователь

    context = {
        "orders": user_orders
    }

    return render(request, "orders_list.html", context=context)


def order_detail(request, order_id):
    """Показываем детали заказа (для авторизованных и анонимных пользователей)"""
    guest_id = get_guest_id(request)

    # Проверяем, есть ли этот заказ у пользователя или гостя
    order = get_object_or_404(Order, id=order_id)

    if request.user.is_authenticated:
        if order.user != request.user:
            return render(request, "403.html")  # Доступ запрещён
    else:
        if order.guest_id != guest_id:
            return render(request, "403.html")  # Доступ запрещён

    context = {
        "order": order
    }

    return render(request, "order_detail.html", context=context)


def cart_add(request, product_id):
    """Добавление товара в корзину с учетом количества"""
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get("quantity", 1))  # Получаем количество из формы

    # Получаем текущую корзину из сессии
    cart = request.session.get("cart", {})

    if str(product_id) in cart:
        cart[str(product_id)]["quantity"] += quantity  # Увеличиваем количество
    else:
        cart[str(product_id)] = {
            "name": product.name,
            "price": str(product.price),  # Django не умеет сериализовать Decimal напрямую
            "quantity": quantity,
            "image": product.image.url if product.image else "",  # Проверка на изображение
        }

    request.session["cart"] = cart  # Обновляем корзину в сессии
    request.session.modified = True  # Помечаем сессию как изменённую

    return redirect("cart")  # Перенаправляем на страницу корзины


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


@login_required
def profile_view(request):
    """Страница профиля пользователя"""
    user = request.user  # Получаем текущего пользователя
    error = None

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()

        # Проверяем, чтобы все данные были корректны
        if not all([full_name, phone, address]):
            error = "Заполните все поля!"
        else:
            user.full_name = full_name
            user.phone = phone
            user.save()

            # Если у пользователя уже есть адрес, обновляем его
            user_address, created = UserAddress.objects.get_or_create(user=user, is_default=True)
            user_address.address = address
            user_address.save()

            return redirect("profile")  # Обновляем страницу

    # Получаем основной адрес пользователя, если он есть
    address = UserAddress.objects.filter(user=user, is_default=True).first()

    context = {
        "user": user,
        "address": address,
        "error": error
    }

    return render(request, "profile.html", context=context)


@login_required
def courier_orders(request):
    """Список заказов для курьера"""
    if not request.user.is_courier:
        return redirect("home")  # Не курьер? На главную!

    orders = Order.objects.filter(courier=request.user).order_by("-created_at")

    context = {
        "orders": orders
    }

    return render(request, "courier_orders.html", context=context)


@login_required
def courier_order_detail(request, order_id):
    """Детали заказа для курьера"""
    if not request.user.is_courier:
        return redirect("home")

    order = get_object_or_404(Order, id=order_id, courier=request.user)

    context = {
        "order": order
    }

    return render(request, "courier_order_detail.html", context=context)


@login_required
def mark_order_delivered(request, order_id):
    """Курьер отмечает заказ как доставленный"""
    if not request.user.is_courier:
        return redirect("home")

    order = get_object_or_404(Order, id=order_id, courier=request.user)
    order.status = "delivered"
    order.save()
    return redirect("courier_orders")


@login_required
def available_orders(request):
    """Выводит все свободные заказы (без назначенного курьера)."""
    if not request.user.is_courier:
        return redirect("home")  # Если не курьер, редиректим

    orders = Order.available_orders()
    return render(request, "available_orders.html", {"orders": orders})


@login_required
def take_order(request, order_id):
    """Курьер берет заказ в работу."""
    if not request.user.is_courier:
        return redirect("home")

    order = get_object_or_404(Order, id=order_id, courier__isnull=True)

    order.courier = request.user  # Назначаем курьера
    order.save()

    return JsonResponse({"success": True, "message": "Вы взяли заказ!"})
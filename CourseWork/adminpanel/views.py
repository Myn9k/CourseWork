import django.contrib.auth

from django import forms
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.apps import apps  # Импортируем модуль для работы с приложениями и моделями в проекте Django
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from main.models import *


from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .forms import get_custom_model_form
from tablib import Dataset
from .decorators import admin_required


def get_models_list():
    """Функция для получения списка моделей"""
    return [
        {
            'name': model._meta.object_name,
            'verbose_name_plural': model._meta.verbose_name_plural
        }
        for model in apps.get_models()
    ]


@admin_required
@login_required
def export_data(request, model_name):
    # Получаем модель по имени
    model = apps.get_model('main', model_name)

    # Динамически создаем ресурс для модели
    DynamicModelResource = type(
        'DynamicModelResource',
        (resources.ModelResource,),
        {'Meta': type('Meta', (object,), {'model': model})}
    )

    model_resource = DynamicModelResource()
    dataset = model_resource.export()

    # Формируем CSV-ответ с данными
    response = HttpResponse(dataset.json, content_type='text/json')
    response['Content-Disposition'] = f'attachment; filename="{model_name}_data.json"'
    return response


@admin_required
@login_required
def import_data(request, model_name):
    # Получаем модель по имени
    model = apps.get_model('main', model_name)

    # Динамически создаем ресурс для модели
    DynamicModelResource = type(
        'DynamicModelResource',
        (resources.ModelResource,),
        {'Meta': type('Meta', (object,), {'model': model})}
    )

    model_resource = DynamicModelResource()

    if request.method == 'POST' and request.FILES.get('file'):
        dataset = Dataset()
        new_data = request.FILES['file']
        dataset.load(new_data.read(), format='json')

        # Импортируем данные
        model_resource.import_data(dataset, dry_run=False)

        return redirect('model_list_view', model_name=model_name)

    context = {'model_name': model_name}
    return render(request, 'admin_panel/import_data.html', context)


# Отображение всех моделей
@admin_required
@login_required
def admin_dashboard(request):
    """
    Функция отображает список всех моделей, зарегистрированных в проекте.
    """
    context = {
        'models': get_models_list()  # Передаем список моделей в шаблон
    }
    # Отправляем данные в шаблон по путю 'admin_panel/dashboard.html'
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@admin_required
def model_list_view(request, model_name):
    # Получаем модель по имени
    model = apps.get_model('main', model_name)

    # Фильтруем данные на основе параметров запроса
    filters = {}
    for field in model._meta.fields:
        field_name = field.name
        field_value = request.GET.get(field_name)
        # Проверяем, что значение не None и не пустая строка
        if field_value not in [None, '', 'None']:
            filters[field_name] = field_value

    # Получаем все записи модели с применением фильтров
    objects = model.objects.filter(**filters)

    # Получаем возможные значения для фильтров
    filter_options = {}
    for field in model._meta.fields:
        # Используем get_internal_type(), чтобы проверять тип поля
        if field.get_internal_type() in ['ForeignKey', 'CharField']:  # Можно расширить для других типов
            # Для ForeignKey собираем значения по связанной модели
            if field.get_internal_type() == 'ForeignKey':
                related_model = field.related_model
                filter_options[field.name] = related_model.objects.all()
            else:
                # Для CharField или других типов собираем уникальные значения
                filter_options[field.name] = model.objects.values_list(field.name, flat=True).distinct()

    context = {
        'objects': objects,
        'model_name': model_name,
        'filter_options': filter_options,
        'models': get_models_list()  # Передаем список моделей в шаблон
    }

    return render(request, 'admin_panel/model_list.html', context)


@login_required
@admin_required
# Редактирование или добавление записи модели
def model_edit_view(request, model_name, object_id=None):
    model = apps.get_model('main', model_name)

    instance = None
    if object_id:
        instance = get_object_or_404(model, id=object_id)

    # Используем пользовательскую форму с Bootstrap классами
    ModelForm = get_custom_model_form(model)

    if request.method == 'POST':
        form = ModelForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('model_list_view', model_name=model_name)
    else:
        form = ModelForm(instance=instance)

    context = {
        'form': form,
        'model_name': model_name,
        'models': get_models_list()  # Передаем список моделей в шаблон
    }

    return render(request, 'admin_panel/model_edit.html', context)


@login_required
@admin_required
def model_delete_view(request, model_name, object_id):
    model = apps.get_model('main', model_name)
    instance = get_object_or_404(model, id=object_id)

    if request.method == 'POST':
        instance.delete()
        return redirect('model_list_view', model_name=model_name)

    context = {
        'object': instance,
        'model_name': model_name
    }

    return render(request, 'admin_panel/model_delete_confirm.html', context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Аутентификация пользователя
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # Входим в систему
            return redirect('home')
        else:
            # Ошибка аутентификации
            return render(request, 'admin_panel/login.html', {'error': 'Неверный логин или пароль'})

    return render(request, 'admin_panel/login.html')


# Логаут
def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    """Страница регистрации"""
    if request.user.is_authenticated:
        return redirect("home")

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "").strip()
        password2 = request.POST.get("password2", "").strip()

        # Проверяем ошибки
        if not all([username, full_name, phone, email, password1, password2]):
            error = "Все поля обязательны!"
        elif password1 != password2:
            error = "Пароли не совпадают!"
        elif User.objects.filter(username=username).exists():
            error = "Логин уже используется!"
        elif User.objects.filter(email=email).exists():
            error = "Email уже зарегистрирован!"
        else:
            # Разбиваем `full_name` на части (без ошибок)
            name_parts = full_name.split()
            last_name = name_parts[0] if len(name_parts) > 0 else ""
            first_name = name_parts[1] if len(name_parts) > 1 else ""

            # Создаём пользователя в модели
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username,
                full_name=full_name,
                phone=phone,
                email=email,
                password=password1,
            )
            login(request, user)  # Авторизуем после регистрации
            return redirect("home")

    return render(request, "admin_panel/register.html", {"error": error})
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.apps import apps

from main.models import *
from .models import *

from django.forms import modelform_factory
from django.core.exceptions import ObjectDoesNotExist


def get_all_models():
    models = apps.get_models()
    filtered_models = []

    for model in models:
        try:
            # Исключаем модель 'User' из приложения 'admin' и проверяем, есть ли записи в модели
            if (model.__name__ != 'User' or model._meta.app_label != 'admin'):
                # Проверяем, есть ли записи в модели
                if model.objects.exists():
                    filtered_models.append(model)
        except ObjectDoesNotExist:
            # Обрабатываем ситуацию, если модель не существует
            pass

    return filtered_models


def get_custom_model_form(model):
    class CustomModelForm(modelform_factory(model, exclude=[])):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field_name, field in self.fields.items():
                if isinstance(field.widget, forms.CheckboxInput):
                    # Добавляем класс для чекбоксов
                    field.widget.attrs.update({'class': 'form-check-input'})
                elif isinstance(field, (forms.DateField, forms.DateTimeField)):
                    field.widget.input_type = 'text'  # Меняем на текст для совместимости с datepicker
                    field.widget = forms.TextInput(attrs={
                        'class': 'form-control datepicker',  # добавляем класс для JS
                        'placeholder': 'Выберите дату',  # подсказка для поля
                        'id': 'date'
                    })
                else:
                    # Добавляем класс для всех остальных полей
                    field.widget.attrs.update({'class': 'form-control'})

    return CustomModelForm


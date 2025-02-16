from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['address']

    def __init__(self, *args, **kwargs):
        """Автоматически подставляем данные пользователя."""
        self.user = kwargs.pop('user', None)  # Получаем пользователя из аргументов
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """Сохраняем заказ и добавляем пользователя."""
        order = super().save(commit=False)
        order.user = self.user  # Привязываем заказ к пользователю
        order.full_name = self.user.full_name  # Берём имя пользователя из модели `User`
        order.phone = self.user.phone  # Берём телефон пользователя из модели `User`

        if commit:
            order.save()
        return order

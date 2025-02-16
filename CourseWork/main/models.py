from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class User(AbstractUser):
    """Расширенная модель пользователя"""
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions",
        blank=True
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["date_joined"]

    def __str__(self):
        return self.full_name


class UserAddress(models.Model):
    """Адреса доставки пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address = models.TextField()
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Адрес пользователя"
        verbose_name_plural = "Адреса пользователей"
        ordering = ['-is_default']

    def __str__(self):
        return f"{self.user.full_name} - {self.address}"


class Ingredient(models.Model):
    """Ингредиенты для блюд"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    base_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (+{self.base_price} руб.)"


class ProductCategory(models.Model):
    """Категории продуктов"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name="subcategories")

    class Meta:
        verbose_name = "Категория продуктов"
        verbose_name_plural = "Категории продуктов"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товары на продажу"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.price} руб."


class ProductIngredient(models.Model):
    """Связь товара с ингредиентами"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    is_optional = models.BooleanField(default=True)
    remove_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Ингредиент продукта"
        verbose_name_plural = "Ингредиенты продуктов"
        ordering = ['product']

    def __str__(self):
        return f"{self.product.name} содержит {self.ingredient.name}"


class Order(models.Model):
    """Заказ пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'В обработке'),
            ('in_delivery', 'Доставляется'),
            ('delivered', 'Доставлено'),
            ('cancelled', 'Отменено'),
        ],
        default='pending'
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def calculate_total_price(self):
        total = sum(item.get_total_price() for item in self.items.all())
        self.total_price = total
        self.save()

    def __str__(self):
        return f"Заказ {self.id} - {self.user.full_name} ({self.get_status_display()})"


class OrderItem(models.Model):
    """Товары в заказе"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказах"

    def get_total_price(self):
        base_price = self.product.price
        customization_price = sum(custom.price for custom in self.customizations.all())
        return (base_price + customization_price) * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Delivery(models.Model):
    """Информация о доставке заказа"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery")
    courier_name = models.CharField(max_length=255, blank=True, null=True)
    courier_phone = models.CharField(max_length=20, blank=True, null=True)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    estimated_delivery = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('waiting', 'Ожидание курьера'),
            ('on_way', 'Курьер в пути'),
            ('delivered', 'Доставлено'),
            ('failed', 'Доставка не удалась')
        ],
        default='waiting'
    )

    class Meta:
        verbose_name = "Доставка"
        verbose_name_plural = "Доставки"

    def __str__(self):
        return f"Доставка заказа {self.order.id} ({self.get_status_display()})"

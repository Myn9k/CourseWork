from django.contrib import admin
from django.utils.text import slugify
from .models import (
    User, UserAddress, Ingredient, ProductCategory, Product,
    ProductIngredient, Order, OrderItem, Delivery
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email', 'phone', 'date_joined', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'full_name', 'email', 'phone')
    ordering = ('-date_joined',)
    fieldsets = (
        ('Личные данные', {'fields': ('username', 'full_name', 'email', 'phone', 'password')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Дополнительная информация', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('user__full_name', 'address')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'image', 'slug')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductIngredient)
class ProductIngredientAdmin(admin.ModelAdmin):
    list_display = ('product', 'ingredient', 'is_optional', 'remove_price')
    list_filter = ('is_optional',)
    search_fields = ('product__name', 'ingredient__name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__full_name', 'id')
    ordering = ('-created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity')
    list_filter = ('order',)
    search_fields = ('order__id', 'product__name')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('order', 'courier_name', 'courier_phone', 'tracking_number', 'status')
    list_filter = ('status',)
    search_fields = ('order__id', 'courier_name', 'tracking_number')

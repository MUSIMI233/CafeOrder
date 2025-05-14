
from django.contrib import admin
from .models import (
    Business, Table, Category, Food,
    Order, OrderDetail, TimedPromotion
)



# 商户模型可由超级用户管理
@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'user', 'is_active']


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['item', 'price', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['item']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category', 'business', 'is_active']
    search_fields = ['category']


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'business', 'is_active']
    search_fields = ['table_number']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'order_status', 'created_time', 'total_price']
    list_filter = ['order_status', 'created_time']
    search_fields = ['id']


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ['order', 'item', 'amount', 'unit_price']


@admin.register(TimedPromotion)
class TimedPromotionAdmin(admin.ModelAdmin):
    list_display = ['food', 'day_of_week', 'start_time', 'end_time', 'discount_price']
    list_filter = ['day_of_week']

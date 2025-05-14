from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class BusinessUser(AbstractUser):
    business_name = models.CharField(max_length=100)

class Business(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_profile')
    business_name = models.CharField(max_length=64)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.business_name
    
class Table(models.Model):
    table_number = models.CharField(max_length=10)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='tables')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('table_number', 'business')

    def __str__(self):
        return f"{self.business.business_name} - {self.table_number}"

class Category(models.Model):
    category = models.CharField(max_length=64)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='categories')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('category', 'business')

    def __str__(self):
        return self.category

class Food(models.Model):
    item = models.CharField(max_length=64)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='food_images/', blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='foods')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('item', 'category')

    def __str__(self):
        return self.item

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        MAKING = 'making', 'Making'
        DONE = 'done', 'Done'
        CANCELLED = 'cancelled', 'Cancelled'

    table = models.ForeignKey('Table', on_delete=models.CASCADE, related_name='orders')
    order_status = models.CharField(max_length=10, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    created_time = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    business = models.ForeignKey('Business', on_delete=models.CASCADE, related_name='orders')

    def __str__(self):
        return f"Order #{self.id} - Table {self.table.table_number}"
    

class OrderDetail(models.Model):
    item = models.ForeignKey('Food', on_delete=models.CASCADE, related_name='order_details')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_details')
    amount = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('item', 'order')

    def __str__(self):
        return f"{self.amount} x {self.item.item} (Order #{self.order.id})"

class TimedPromotion(models.Model):
    food = models.ForeignKey('Food', on_delete=models.CASCADE, related_name='promotions')
    day_of_week = models.CharField(max_length=10)  
    start_time = models.TimeField()
    end_time = models.TimeField()
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    promo_text = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"Promo for {self.food.item} on {self.day_of_week}"

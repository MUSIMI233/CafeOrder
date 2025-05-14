
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    FoodViewSet, OrderViewSet, user_login, user_logout, 
    user_register, dashboard_view, menu_management_view,
    mark_order_done, delete_order, menu_view ,table_management_view
)
from django.shortcuts import redirect


router = DefaultRouter()
router.register(r'food', FoodViewSet, basename='food')     # basename 是必须的
router.register(r'order', OrderViewSet, basename='order')  # 没有 queryset 时必须加

urlpatterns = [
    # 页面视图（HTML）
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', user_register, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/menu/', menu_management_view, name='menu_management'),
    path('dashboard/mark_done/<int:order_id>/', mark_order_done, name='mark_order_done'),
    path('dashboard/delete/<int:order_id>/', delete_order, name='delete_order'),
    path('dashboard/tables/', table_management_view, name='table_management'),
    
    path('menu/', menu_view, name='menu'),
    # API 路由前缀：/api/food/, /api/order/
    path('api/', include(router.urls)),
]

def redirect_login(request):
    return redirect('/login/')

urlpatterns += [
    path('accounts/login/', redirect_login),  # 👈 兼容跳转
]

import os
import qrcode

from django.conf import settings

def generate_qr_code(business_id, table_number):
    """
    Generate QR code for a specific table number
    
    Args:
        business_id: The ID of the business 
        table_number: The table number to generate QR for
        
    Returns:
        str: The path to the saved QR code image relative to MEDIA_ROOT
    """
    # Create URL with table parameter
    url = f"{settings.BASE_URL}/menu/?table={table_number}&business={business_id}"
    
    # Generate QR code
    qr = qrcode.make(url)
    
    # Create directory if it doesn't exist
    qr_code_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
    os.makedirs(qr_code_dir, exist_ok=True)
    
    # Create unique filename (business_id-table_number.png)
    filename = f"table_{business_id}_{table_number}.png"
    filepath = os.path.join(qr_code_dir, filename)
    
    # Save QR code image
    qr.save(filepath)
    
    # Return path relative to MEDIA_ROOT
    return f"qr_codes/{filename}"


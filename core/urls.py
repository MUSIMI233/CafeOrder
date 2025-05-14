# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    FoodViewSet, OrderViewSet, user_login, user_logout, 
    user_register, dashboard_view, menu_management_view,
    mark_order_done, delete_order, menu_view 
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
    
    path('menu/', menu_view, name='menu'),
    # API 路由前缀：/api/food/, /api/order/
    path('api/', include(router.urls)),
]

def redirect_login(request):
    return redirect('/login/')

urlpatterns += [
    path('accounts/login/', redirect_login),  # 👈 兼容跳转
]
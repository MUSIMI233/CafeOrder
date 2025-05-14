# views.py - 商家登录、注册、Dashboard 权限控制完整版本

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django import forms

from .forms import BusinessUserCreationForm
from .models import Business, Food, Order, Category, TimedPromotion,Table
from .serializers import OrderSerializer, OrderSubmissionSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.http import HttpResponse


User = get_user_model()

# ============ 注册 ============
def user_register(request):
    if request.method == 'POST':
        form = BusinessUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.save()

            business_name = form.cleaned_data.get('business_name')
            email = form.cleaned_data.get('email')

            Business.objects.create(
                user=user,
                business_name=business_name,
                email=email
            )

            login(request, user)
            return redirect('/dashboard/')
    else:
        form = BusinessUserCreationForm()
    return render(request, 'register.html', {'form': form})


# ============ 登录 ============
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                return redirect('/admin/')  # 管理员跳转 admin
            login(request, user)
            return redirect('/dashboard/')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# ============ 登出 ============
def user_logout(request):
    logout(request)
    return redirect('/login/')

# ============ Dashboard ============
@login_required
def dashboard_view(request):
    if request.user.is_staff:
        return redirect('/admin/')
    business = get_object_or_404(Business, user=request.user)
    food_items = Food.objects.filter(category__business=business)

    orders = Order.objects.filter(business=business).prefetch_related('order_details__item', 'table')

    return render(request, 'dashboard/dashboard.html', {
        'food_items': food_items,
        'business': business,
        'orders': orders  
    })

# ============ 菜单管理 ============
@login_required
def menu_management_view(request):
    business = get_object_or_404(Business, user=request.user)
    categories = Category.objects.filter(business=business)
    food_items = Food.objects.filter(category__business=business)

    # 表单定义
    class FoodForm(forms.ModelForm):
        class Meta:
            model = Food
            fields = ['item', 'price', 'description', 'category', 'image']

    class PromoForm(forms.ModelForm):
        class Meta:
            model = TimedPromotion
            fields = ['day_of_week', 'start_time', 'end_time', 'discount_price', 'promo_text']
            # 关键修改：所有字段设为不必填
            widgets = {
                'day_of_week': forms.TextInput(attrs={'required': False}),
                'start_time': forms.TimeInput(attrs={'required': False}),
                'end_time': forms.TimeInput(attrs={'required': False}),
                'discount_price': forms.NumberInput(attrs={'required': False}),
                'promo_text': forms.TextInput(attrs={'required': False}),
            }

    class CategoryForm(forms.ModelForm):
        class Meta:
            model = Category
            fields = ['category']

    # 处理删除分类请求
    if 'delete_category' in request.POST:
        category_id = request.POST.get('category_id')
        try:
            category = Category.objects.get(id=category_id, business=business)
            category_name = category.category
            
            # 删除分类将同时删除该分类下的所有菜品
            # 如果你不想删除菜品，可以选择将它们移到默认分类或将分类标记为不活跃而不是删除
            category.delete()
            
            messages.success(request, f"Category '{category_name}' and all its foods have been deleted.")
        except Category.DoesNotExist:
            messages.error(request, "Category not found.")
        return redirect('menu_management')
    
    #删除
    
    if 'delete_food' in request.POST:
        food_id = request.POST.get('food_id')
        try:
            food = Food.objects.get(id=food_id, category__business=business)
            food_name = food.item
            food.delete()
            messages.success(request, f"Food item '{food_name}' has been deleted.")
        except Food.DoesNotExist:
            messages.error(request, "Food item not found.")
        return redirect('menu_management')

    # 添加分类
    if 'add_category' in request.POST:
        category_form = CategoryForm(request.POST)
        if category_form.is_valid():
            new_cat = category_form.save(commit=False)
            new_cat.business = business
            new_cat.is_active = True
            new_cat.save()
            messages.success(request, f"Category '{new_cat.category}' added.")
            return redirect('menu_management')
    else:
        category_form = CategoryForm()

    # 上传菜品 + 促销
    if request.method == 'POST' and 'add_category' not in request.POST:
        food_form = FoodForm(request.POST, request.FILES)
        promo_form = PromoForm(request.POST)

        if food_form.is_valid():
            new_food = food_form.save(commit=False)
            new_food.category = food_form.cleaned_data['category']
            new_food.is_active = True  # 设置为活动状态
            new_food.save()

            # 检查是否有任何促销信息被填写
            has_promo_data = False
            promo_data = {
                'day_of_week': request.POST.get('day_of_week', '').strip(),
                'start_time': request.POST.get('start_time', '').strip(),
                'end_time': request.POST.get('end_time', '').strip(),
                'discount_price': request.POST.get('discount_price', '').strip(),
                'promo_text': request.POST.get('promo_text', '').strip()
            }
            
            # 检查是否有任何促销字段被填写
            has_promo_data = any(value for value in promo_data.values())
            
            # 只有在有促销数据的情况下才创建促销记录
            if has_promo_data and promo_form.is_valid():
                new_promo = promo_form.save(commit=False)
                new_promo.food = new_food
                new_promo.save()
                messages.success(request, f"{new_food.item} with promotion uploaded successfully.")
            else:
                messages.success(request, f"{new_food.item} uploaded successfully.")
                
            return redirect('menu_management')
        else:
            # 如果菜品表单不有效，向用户显示错误信息
            for field, errors in food_form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        food_form = FoodForm()
        promo_form = PromoForm()

    # 表单样式统一
    for field in food_form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})
    for field in promo_form.fields.values():
        field.widget.attrs.update({'class': 'form-control', 'required': False})  # 设置为不必填
    for field in category_form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})

    return render(request, 'dashboard/menu.html', {
        'food_form': food_form,
        'promo_form': promo_form,
        'category_form': category_form,
        'categories': categories,
    })

# ============ 标记订单完成 ============
@login_required
def mark_order_done(request, order_id):
    order = get_object_or_404(Order, id=order_id, business=request.user.business_profile)
    order.order_status = Order.OrderStatus.DONE
    order.save()
    messages.success(request, f"Order #{order_id} marked as done.")
    return redirect('dashboard')

# ============ 删除订单 ============
@login_required
@require_POST
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect('dashboard')

# ============ 客户端菜单页面 ============
# Update menu_view in views.py
def menu_view(request):
    # Get business ID and table number from query parameters
    business_id = request.GET.get('business')
    table_number = request.GET.get('table')
    
    # Validate parameters
    if not business_id or not table_number:
        # Handle missing parameters - redirect to error page or show message
        return HttpResponse("Invalid QR code. Missing table or business information.")
    
    try:
        # Get business and validate table exists
        business = get_object_or_404(Business, id=business_id)
        table = get_object_or_404(Table, business=business, table_number=table_number)
        
        # Get active categories for this business
        categories = Category.objects.filter(business=business, is_active=True)
        
        return render(request, 'client/index.html', {
            'categories': categories,
            'table_number': table_number,
            'business': business
        })
    except (Business.DoesNotExist, Table.DoesNotExist):
        return render(request, 'client/error.html', {
            'message': 'Invalid table or business information.'
        })


# ============ API ============
from rest_framework import viewsets
from .serializers import FoodSerializer, OrderSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

class FoodViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FoodSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context
    
    def get_permissions(self):
        if self.request.query_params.get('business_id'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        business_id = self.request.query_params.get('business_id')
        
        if business_id:
            return Food.objects.filter(
                category__business_id=business_id, 
                is_active=True
            )
        
        user = self.request.user
        try:
            business = Business.objects.get(user=user)
        except Business.DoesNotExist:
            return Food.objects.none()
        return Food.objects.filter(category__business=business, is_active=True)

@method_decorator(csrf_exempt, name='dispatch')
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]  # 允许匿名订单

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderSubmissionSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        try:
            business = Business.objects.get(user=user)
        except Business.DoesNotExist:
            return Order.objects.none()
        return Order.objects.filter(table__business=business)
        
    def create(self, request, *args, **kwargs):
        import json
        
        print("=" * 50)
        print("接收到订单请求")
        
        # 打印请求数据
        try:
            if hasattr(request, 'body'):
                print("请求体:", request.body.decode('utf-8'))
            print("请求数据:", request.data)
            for key, value in request.data.items():
                print(f"  {key}: {value} (类型: {type(value)})")
        except Exception as e:
            print(f"打印请求数据时出错: {str(e)}")
        
        try:
            # 获取序列化器并验证数据
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print("验证错误:", serializer.errors)
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print("验证通过的数据:", serializer.validated_data)
            
            # 创建订单
            try:
                instance = serializer.save()
                print(f"订单创建成功: ID={instance.id}")
                return Response(
                    serializer.data, 
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                import traceback
                print(f"保存订单时出错: {str(e)}")
                print(traceback.format_exc())
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            import traceback
            print(f"处理订单时出错: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        



# QR code 
import qrcode
from django.conf import settings
import os

# Add to views.py

@login_required
def table_management_view(request):
    """View for managing tables"""
    business = get_object_or_404(Business, user=request.user)
    tables = Table.objects.filter(business=business)
    
    # Define table form
    class TableForm(forms.ModelForm):
        class Meta:
            model = Table
            fields = ['table_number']
    
    # Process form submission
    if request.method == 'POST':
        # Handle delete table request
        if 'delete_table' in request.POST:
            table_id = request.POST.get('table_id')
            try:
                table = Table.objects.get(id=table_id, business=business)
                table_number = table.table_number
                table.delete()
                messages.success(request, f"Table {table_number} has been deleted.")
            except Table.DoesNotExist:
                messages.error(request, "Table not found.")
            return redirect('table_management')
        
        # Handle add table request
        elif 'add_table' in request.POST:
            form = TableForm(request.POST)
            if form.is_valid():
                table_number = form.cleaned_data['table_number']
                
                # Check if table already exists for this business
                if Table.objects.filter(business=business, table_number=table_number).exists():
                    messages.error(request, f"Table {table_number} already exists.")
                else:
                    new_table = form.save(commit=False)
                    new_table.business = business
                    new_table.is_active = True
                    new_table.save()
                    messages.success(request, f"Table {table_number} added successfully.")
                return redirect('table_management')
    else:
        form = TableForm()
    
    # Add form styling
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})
    
    return render(request, 'dashboard/tables.html', {
        'tables': tables,
        'form': form,
        'business': business
    })

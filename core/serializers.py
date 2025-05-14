from rest_framework import serializers
from .models import Food, Order, OrderDetail

class FoodSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.category', read_only=True)
    
    class Meta:
        model = Food
        fields = ['id', 'item', 'price', 'description', 'image', 'category', 'category_name']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation['image']:
            # 确保图片URL是完整的
            request = self.context.get('request')
            if request is not None:
                representation['image'] = request.build_absolute_uri(representation['image'])
        return representation

class OrderDetailSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField()

    class Meta:
        model = OrderDetail
        fields = ['item_id', 'amount', 'unit_price']

class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailSerializer(many=True)

    class Meta:
        model = Order
        fields = ['table', 'business', 'total_price', 'order_details']

    def create(self, validated_data):
        details = validated_data.pop('order_details')
        order = Order.objects.create(**validated_data)
        for detail in details:
            item = Food.objects.get(id=detail['item_id'])
            OrderDetail.objects.create(
                order=order,
                item=item,
                amount=detail['amount'],
                unit_price=detail['unit_price']
            )
        return order

class OrderSubmissionSerializer(serializers.Serializer):
    table_number = serializers.CharField(required=True)
    items = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    def validate_items(self, items):
        # 检查每个项目是否具有所需字段
        for i, item in enumerate(items):
            if 'item_id' not in item:
                raise serializers.ValidationError(f"位置{i}的项目缺少'item_id'")
            if 'amount' not in item:
                raise serializers.ValidationError(f"位置{i}的项目缺少'amount'")
        return items

    def create(self, validated_data):
        from .models import Table, Business, Order, OrderDetail, Food
        
        print("创建订单，验证后的数据:", validated_data)  # 调试输出
        
        table_number = validated_data.get('table_number')
        if not table_number:
            raise serializers.ValidationError("桌号不能为空")
            
        items = validated_data.get('items', [])
        if not items:
            raise serializers.ValidationError("订单项目不能为空")

        # 获取第一个食品项目以找到关联的业务
        try:
            first_item_id = items[0].get('item_id')
            if not first_item_id:
                raise serializers.ValidationError("第一个项目缺少item_id")
                
            first_item = Food.objects.get(id=first_item_id)
            business = first_item.category.business
        except Food.DoesNotExist:
            raise serializers.ValidationError(f"找不到ID为{items[0].get('item_id')}的食品项目")
        except Exception as e:
            raise serializers.ValidationError(f"处理食品项目时出错: {str(e)}")

        # 查找或创建桌子
        try:
            print(f"查找或创建桌子 #{table_number} 对应业务ID {business.id}")
            table, created = Table.objects.get_or_create(
                table_number=table_number,
                business=business
            )
            print(f"桌子 {'创建' if created else '已存在'}: {table.id}")
        except Exception as e:
            print(f"创建桌子时出错: {str(e)}")
            raise serializers.ValidationError(f"创建桌子时出错: {str(e)}")

        # 计算总价
        total_price = 0
        for item in items:
            food = Food.objects.get(id=item['item_id'])
            total_price += food.price * item['amount']

        # 创建订单
        try:
            order = Order.objects.create(
                table=table,
                business=business,
                total_price=total_price
            )
            print(f"创建订单成功: {order.id}")
        except Exception as e:
            print(f"创建订单时出错: {str(e)}")
            raise serializers.ValidationError(f"创建订单时出错: {str(e)}")

        # 创建订单详情
        for item in items:
            try:
                food = Food.objects.get(id=item['item_id'])
                OrderDetail.objects.create(
                    order=order,
                    item=food,
                    amount=item['amount'],
                    unit_price=food.price
                )
            except Exception as e:
                print(f"创建订单详情时出错: {str(e)}")
                # 继续处理其他项目，不要因为一个项目失败而中断整个订单
        
        return order

    def to_representation(self, instance):
        """
        自定义返回值
        """
        from rest_framework import serializers
        
        # 创建一个基本的表示
        ret = {
            'id': instance.id,
            'total_price': instance.total_price,
            'order_status': instance.order_status,
            'created_at': instance.created_at.isoformat() if hasattr(instance, 'created_at') else None,
            'table_number': instance.table.table_number
        }
        
        # 添加订单详情
        details = []
        for detail in instance.order_details.all():
            details.append({
                'id': detail.id,
                'item_name': detail.item.item,
                'amount': detail.amount,
                'unit_price': detail.unit_price
            })
        ret['details'] = details
        
        return ret
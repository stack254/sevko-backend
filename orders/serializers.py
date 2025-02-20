import logging
from rest_framework import serializers
from products.models import Order, OrderItem, Product

logger = logging.getLogger(__name__)

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'email', 'items', 'shipping_details', 'payment_method', 'total_price', 'status', 'created_at', 'updated_at']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    def validate(self, data):
        logger.info(f"Validating order data: {data}")
        if not data.get('email') and not self.context['request'].user.is_authenticated:
            raise serializers.ValidationError("Email is required for guest checkout.")
        if not data.get('shipping_details'):
            raise serializers.ValidationError("Shipping details are required.")
        if not data.get('payment_method'):
            raise serializers.ValidationError("Payment method is required.")
        return data

    def create(self, validated_data):
        logger.info(f"Creating order with validated data: {validated_data}")
        items_data = validated_data.pop('items')
        try:
            order = Order.objects.create(**validated_data)
            for item_data in items_data:
                OrderItem.objects.create(order=order, **item_data)
            return order
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}", exc_info=True)
            raise serializers.ValidationError(f"Error creating order: {str(e)}")
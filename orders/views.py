from django.core.mail import send_mail
import logging
from rest_framework import viewsets
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from products.models import Order, OrderItem
from .serializers import *
import smtplib



@api_view(['POST'])
def create_order(request):
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        order = serializer.save()
        
        # Create order items
        items_data = request.data.get('items', [])
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                price=item_data['price']
            )
        
        # Recalculate total price
        order.total_price = sum(item.price * item.quantity for item in order.items.all())
        order.save()
        
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def notify_seller(request):
    order_id = request.data.get('orderId')
    try:
        order = Order.objects.get(id=order_id)
        
        # Compose email
        subject = f'New Order #{order.id}'
        message = f'''
        A new order has been placed:
        
        Order ID: {order.id}
        Total: KES {order.total_price}
        Items:
        {', '.join([f"{item.product.name} (x{item.quantity}) - KES {item.price * item.quantity}" for item in order.items.all()])}
        
        Shipping Details:
        {order.shipping_details}
        '''
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [settings.SELLER_EMAIL]  # Make sure to set this in your settings.py
        
        # Send email
        send_mail(subject, message, from_email, recipient_list)
        
        return Response({'status': 'Seller notified'}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # If user is authenticated, associate the order with the user
        if request.user.is_authenticated:
            serializer.save(user=request.user)
        else:
            serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        return Order.objects.filter(email=self.request.query_params.get('email', ''))
   
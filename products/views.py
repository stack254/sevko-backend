
from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import AnonymousUser
import logging
from .models import Product, Category, Order, OrderItem, Cart, CartItem
from .serializers import ProductSerializer, CategorySerializer, OrderSerializer, CartSerializer
from .pagination import ProductPagination

logger = logging.getLogger(__name__)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Category filter
        if category := self.request.query_params.get('category'):
            category_ids = category.split(',')
            queryset = queryset.filter(category__id__in=category_ids)
        
        # Price range filter
        if min_price := self.request.query_params.get('min_price'):
            queryset = queryset.filter(price__gte=min_price)
        if max_price := self.request.query_params.get('max_price'):
            queryset = queryset.filter(price__lte=max_price)
        
        # Search filter
        if search := self.request.query_params.get('search'):
            queryset = queryset.filter(name__icontains=search)
        
        # Ordering
        if ordering := self.request.query_params.get('ordering'):
            queryset = queryset.order_by(ordering)
        
        return queryset

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        parent_id = self.request.query_params.get('parent', None)
        if parent_id is not None:
            queryset = queryset.filter(parent_id=parent_id)
        return queryset

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


@api_view(['POST'])
def create_order(request):
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        order = serializer.save()
        
        # Create order items
        items_data = request.data.get('items', [])
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product_id=item_data['product_id'],
                quantity=item_data['quantity']
            )
        
        # Handle different payment methods
        payment_method = request.data.get('payment_method')
        if payment_method == 'cod':
            order.status = 'Pending'  # or whatever status you use for COD orders
        elif payment_method == 'whatsapp':
            order.status = 'Awaiting Payment'  # or whatever status you use for WhatsApp orders
        
        order.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryDetail(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            logger.info(f"Retrieved category: {instance.id}")
            return Response(serializer.data)
        except Category.DoesNotExist:
            logger.error(f"Category not found for ID: {kwargs.get('pk')}")
            return Response(
                {"error": "Category not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving category: {str(e)}")
            return Response(
                {"error": "An error occurred while retrieving the category"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        return Cart.objects.filter(session_id=self.request.session.session_key)

    def get_object(self):
        cart = None
        if self.request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
        else:
            session_id = self.request.session.session_key
            if not session_id:
                self.request.session.create()
                session_id = self.request.session.session_key
            cart, _ = Cart.objects.get_or_create(session_id=session_id)
        return cart
    
    @action(detail=False, methods=['get'])
    def view_cart(self, request):
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_to_cart(self, request):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        if product.stock < quantity:
            return Response({'error': 'Not enough stock'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    

  
    @action(detail=False, methods=['put'])
    def update_quantity(self, request):
        print("Update quantity action called")
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 0))

        try:
            cart_item = CartItem.objects.get(id=item_id)
            
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                # If quantity is 0 or negative, remove the item
                cart_item.delete()

            cart = cart_item.cart
            cart.refresh_from_db()
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@action(detail=False, methods=['POST'])
def remove_from_cart(self, request):
    print("Remove from cart action called")
    print(f"Request method: {request.method}")
    print(f"Request data: {request.data}")

    item_id = request.data.get('item_id')
    if not item_id:
        return Response({'error': 'item_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get the current user's cart
        cart = self.get_object()
        print(f"Cart found: {cart.id}")
        
        # Check if the item exists in any cart
        if CartItem.objects.filter(id=item_id).exists():
            item = CartItem.objects.get(id=item_id)
            
            # If the item belongs to a different cart, handle it appropriately
            if item.cart.id != cart.id:
                print(f"Item {item_id} belongs to cart {item.cart.id}, not the current cart {cart.id}")
                
                # Option 1: Return an error
                # return Response({'error': 'Item belongs to a different cart'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Option 2: Check if the product exists in the current cart and remove that instead
                try:
                    product_id = item.product.id
                    current_cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
                    print(f"Found equivalent item {current_cart_item.id} in current cart")
                    current_cart_item.delete()
                    print(f"Equivalent item deleted successfully")
                    cart.refresh_from_db()
                    serializer = self.get_serializer(cart)
                    return Response(serializer.data)
                except CartItem.DoesNotExist:
                    return Response({'error': 'Item not found in your cart'}, status=status.HTTP_404_NOT_FOUND)
            else:
                # Item belongs to the current cart, proceed with deletion
                print(f"Item found: {item.id}, product: {item.product.name if hasattr(item.product, 'name') else 'Unknown'}")
                item.delete()
                print(f"Item deleted successfully")
                cart.refresh_from_db()
                serializer = self.get_serializer(cart)
                return Response(serializer.data)
        else:
            print(f"Item {item_id} does not exist in any cart")
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class ProductList(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = ProductPagination

    def get_queryset(self):
        queryset = Product.objects.all()
        
        # Category filter
        if category := self.request.query_params.get('category'):
            category_ids = category.split(',')
            queryset = queryset.filter(category__id__in=category_ids)
        
        # Price range filter
        if min_price := self.request.query_params.get('min_price'):
            queryset = queryset.filter(price__gte=min_price)
        if max_price := self.request.query_params.get('max_price'):
            queryset = queryset.filter(price__lte=max_price)
        
        # Search filter
        if search := self.request.query_params.get('search'):
            queryset = queryset.filter(name__icontains=search)
        
        # Ordering
        if ordering := self.request.query_params.get('ordering'):
            queryset = queryset.order_by(ordering)
        
        return queryset

    
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'

class CartView(APIView):
    def get_or_create_cart(self, request):
        if not isinstance(request.user, AnonymousUser):
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_id=request.session.session_key)
        return cart

    def get(self, request):
        cart = self.get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def post(self, request):
        cart = self.get_or_create_cart(request)
        action = request.data.get('action')
        
        if action == 'add':
            return self.add_to_cart(request, cart)
        elif action == 'remove':
            return self.remove_from_cart(request, cart)
        elif action == 'update':
            return self.update_quantity(request, cart)
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
    
    def add_to_cart(self, request, cart):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if product.stock < quantity:
            return Response({'error': 'Not enough stock'}, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def remove_from_cart(self, request, cart):
        item_id = request.data.get('item_id')
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            cart.refresh_from_db()
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found in cart'}, status=status.HTTP_404_NOT_FOUND)
    
    def update_quantity(self, request, cart):
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 0))
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                # If quantity is 0 or negative, remove the item
                cart_item.delete()
            
            cart.refresh_from_db()
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

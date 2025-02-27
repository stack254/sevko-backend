

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        return Cart.objects.filter(session_id=self.request.session.session_key)
def get_or_create_cart(request):
    """Helper function to get or create a cart based on user authentication status"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For anonymous users, use session ID
        session_id = request.session.get('cart_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['cart_id'] = session_id
        
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    
    return cart

@api_view(['GET'])
@permission_classes([AllowAny])
def view_cart(request):
    """View the current cart"""
    cart = get_or_create_cart(request)
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart(request):
    """Add a product to the cart"""
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    
    if not product_id:
        return Response(
            {'error': 'Product ID is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if product is in stock
    if not product.is_in_stock(quantity):
        return Response(
            {'error': f'Only {product.stock} items available in stock'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    cart = get_or_create_cart(request)
    
    # Check if product already in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    # If product already exists in cart, update quantity
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_quantity(request):
    """Update the quantity of a cart item"""
    item_id = request.data.get('item_id')
    quantity = request.data.get('quantity')
    
    if not item_id or quantity is None:
        return Response(
            {'error': 'Item ID and quantity are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return Response(
                {'error': 'Quantity must be greater than 0'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except ValueError:
        return Response(
            {'error': 'Quantity must be a number'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    cart = get_or_create_cart(request)
    
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        
        # Check if requested quantity is available in stock
        if not cart_item.product.is_in_stock(quantity):
            return Response(
                {'error': f'Only {cart_item.product.stock} items available in stock'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    except CartItem.DoesNotExist:
        return Response(
            {'error': 'Cart item not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def remove_from_cart(request):
    """Remove an item from the cart"""
    item_id = request.data.get('item_id')
    
    if not item_id:
        return Response(
            {'error': 'Item ID is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    cart = get_or_create_cart(request)
    
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    except CartItem.DoesNotExist:
        return Response(
            {'error': 'Cart item not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([AllowAny])
def clear_cart(request):
    """Remove all items from the cart"""
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def merge_carts(request):
    """Merge anonymous cart with user cart after login"""
    # Get session cart ID
    session_id = request.session.get('cart_id')
    
    if not session_id:
        # No session cart to merge
        return Response({'message': 'No anonymous cart to merge'})
    
    try:
        # Get session cart
        session_cart = Cart.objects.get(session_id=session_id)
        
        # Get or create user cart
        user_cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Merge items from session cart to user cart
        for session_item in session_cart.items.all():
            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=session_item.product,
                defaults={'quantity': session_item.quantity}
            )
            
            if not created:
                user_item.quantity += session_item.quantity
                user_item.save()
        
        # Delete session cart
        session_cart.delete()
        
        # Clear session cart ID
        del request.session['cart_id']
        
        serializer = CartSerializer(user_cart)
        return Response(serializer.data)
    except Cart.DoesNotExist:
        return Response({'message': 'No anonymous cart to merge'})
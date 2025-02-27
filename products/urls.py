from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import CategoryDetail, ProductList, ProductDetailView, ProductDetailView, CartViewSet
from products.views import CartViewSet


router = DefaultRouter()

router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')






urlpatterns = [
    path('', include(router.urls)),
    path('categories/<int:pk>/', CategoryDetail.as_view(), name='category-detail'),
     path('products/', ProductList.as_view(), name='product-list'),
     path('products/<int:id>/', ProductDetailView.as_view(), name='product-detail'),
     path('create/', views.create_order, name='create_order'),
     path('cart/', views.CartView.as_view(), name='cart'),


    
]
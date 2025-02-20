from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrderViewSet.as_view({'get': 'list', 'post': 'create'}), name='order-list'),
    path('<int:pk>/', views.OrderViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='order-detail'),
    path('create/', views.create_order, name='create_order'),
    path('/orders/notify-seller/', views.notify_seller, name='notify_seller'),
]
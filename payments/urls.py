from django.urls import path
from . import views

urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('verify/<str:reference>/', views.verify_payment, name='verify_payment'),
]
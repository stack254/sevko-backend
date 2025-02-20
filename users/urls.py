from django.urls import path
from . import views
from .views import UserProfileView

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('me/', views.UserProfileView.as_view(), name='user-profile'),
  

]
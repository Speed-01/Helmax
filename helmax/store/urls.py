from django.urls import path
# from .views import SignUpView,LoginView
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('logout/', views.logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
   
    path('auth-receiver/', views.auth_receiver, name='auth_receiver'),


 
    
    
]
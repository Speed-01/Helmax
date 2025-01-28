from django.urls import path
from . import views


urlpatterns = [
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('', views.login, name='login'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('logout/', views.logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
   
    path('auth-receiver/', views.auth_receiver, name='auth_receiver'),




    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/variant/<int:variant_id>/', views.get_variant_data, name='get_variant_data'),
    
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    



    ######## CART ########  
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/move-to-wishlist/<int:item_id>/', views.move_to_wishlist, name='move_to_wishlist'),


    ######### Address ########
    path('userManageAddress/', views.userManageAddress, name='userManageAddress'),
    path('editAddress/<int:address_id>/', views.editAddress, name='editAddress'),
    path('deleteAddress/<int:address_id>/', views.deleteAddress, name='deleteAddress'),
    path('set_primary_address/', views.set_primary_address, name='set_primary_address'),


    ######### cheout ########
    path('checkout/', views.user_checkout, name='user_checkout'),
    


    path('place-order/', views.place_order, name='place_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

]
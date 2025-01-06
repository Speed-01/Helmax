from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static




urlpatterns = [
    # Authentication URLs
    path('login/', views.adminLogin, name='adminLogin'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Customer Management
    path('customers/', views.customers, name='customers'),
    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    
    # Product Management
    path('adminProducts/', views.adminProducts, name='adminProducts'),
    path('addProducts/', views.addProducts, name='addProducts'),
    # path('deleteProduct/<int:pk>/', views.deleteProduct, name='deleteProduct'),
    path('addVariant/', views.addVariant, name='addVariant'),
    

    path('admin_category/',views.admin_category,name="admin_category"),
    path('addcategory/',views.add_category,name="add_category"),
    path('edit_category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('toggle_category_status/<int:category_id>/', views.toggle_category_status, name='toggle_category_status'),


    # Brand Management 
    path('admin_brands/', views.admin_brand, name='admin_brand'),
    path('admin_brands/add/', views.add_brand, name='add_brand'),
    path('admin_brands/edit/<int:brand_id>/', views.edit_brand, name='edit_brand'),
    path('admin_brands/toggle/<int:brand_id>/', views.toggle_brand_status, name='toggle_brand_status'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
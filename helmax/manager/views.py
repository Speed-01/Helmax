from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from PIL import Image
from django.core.paginator import Paginator
from .models import Product,Category,ProductImage,User, Brand




from django.conf import settings
import os
from django.core.files.storage import default_storage

from django.contrib.auth.decorators import login_required







@never_cache
def adminLogin(request):
    if request.user.is_authenticated:
        return redirect("admin_dashboard")
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(request, "Invalid username or password")
            return redirect("adminLogin")
        elif user and user.is_superuser:
            login(request, user)
            return redirect("admin_dashboard")
        else:
            messages.error(request, f"{user} have no access to this page")
            return redirect("adminLogin")
    return render(request, "adminLogin.html")

@never_cache

def admin_logout(request):
    logout(request)
    return redirect('adminLogin')




def admin_dashboard(request):
    return render(request, 'adminDashboard.html')



def customers(request):
    if "value" in request.GET:
        credential = request.GET["value"]
        data = User.objects.filter(
            Q(username__icontains=credential) | Q(email__icontains=credential)
        ).values('id', 'username', 'email', 'is_active', 'date_joined')
        context = {"data": data}
    else:
        data = User.objects.all().exclude(is_superuser=True).values('id', 'username', 'email', 'is_active', 'date_joined')
        context = {"data": data}
    return render(request, "customers.html", context)



def toggle_user_status(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if not user.is_superuser:  # Prevent toggling superuser status
            user.is_active = not user.is_active
            user.save()
            return JsonResponse({
                'success': True,
                'status': 'active' if user.is_active else 'blocked'
            })
    return JsonResponse({'success': False}, status=400)
        


def admin_category(request):
    
    categories = Category.objects.all().order_by("-id")
    return render(request, 'admincategory.html', {'categories': categories})

def add_category(request):
    if request.method == "POST":
        name = request.POST.get('category_name')
        if name:  # Ensure the category name is not empty
            if Category.objects.filter(name__iexact=name).exists():
                # If category name already exists, send an error message
                error_message = "Category with this name already exists."
                return render(request, 'admincategory.html', {
                    'categories': Category.objects.all(),
                    'error_message': error_message,
                    'show_add_modal': True,  # Flag to re-show the modal
                })
            else:
                Category.objects.create(name=name)
                print("Category added successfully")
        return redirect('admin_category')  # Use named URL instead of function reference
    return redirect('admin_category')



def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        name = request.POST.get('category_name')
        if name:
            if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
                error_message = "Category with this name already exists."
                return render(request, 'admincategory.html', {
                    'categories': Category.objects.all(),
                    'error_message': error_message,
                    'edit_category': category,
                    'show_edit_modal': True,
                })
            else:
                category.name = name
                category.save()
                print("Category updated successfully")
        return redirect('admin_category')
    return render(request, 'edit_category.html', {'category': category})




def toggle_category_status(request,category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category.is_active = not category.is_active
        category.save()
        return JsonResponse({
            'success': True,
            'status': 'active' if category.is_active else 'blocked'
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)



# def delete_category(request, category_id):
#     category = get_object_or_404(Category, id=category_id)
#     category.is_deleted = True
#     category.save()
#     print("Category deleted successfully")
#     return redirect('admin_category')



def admin_brand(request):
    brands = Brand.objects.all().order_by("-id")
    return render(request, 'adminBrand.html', {'brands': brands})

def add_brand(request):
    if request.method == "POST":
        name = request.POST.get('brand_name')
        if name and not Brand.objects.filter(name__iexact=name).exists():
            Brand.objects.create(name=name)
        return redirect('admin_brand')
    return redirect('admin_brand')

def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    if request.method == "POST":
        name = request.POST.get('brand_name')
        if name and not Brand.objects.filter(name__iexact=name).exclude(id=brand_id).exists():
            brand.name = name
            brand.save()
        return redirect('admin_brand')
    return render(request, 'editBrand.html', {'brand': brand})

def toggle_brand_status(request, brand_id):
    if request.method == 'POST':
        brand = get_object_or_404(Brand, id=brand_id)
        brand.is_active = not brand.is_active
        brand.save()
        return JsonResponse({
            'success': True,
            'status': 'active' if brand.is_active else 'blocked'
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)







from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Product, Category, Variant, ProductImage
from django.http import JsonResponse

def adminProducts(request):
    # products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('variants__sizes', 'variants__images')
    products = Product.objects.filter(is_active=True)
    paginator = Paginator(products, 10)  # 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'adminProducts.html', {'page_obj': page_obj})

def addProducts(request):
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name')
        brand = request.POST.get('brand')
        category = request.POST.get('category')
        description = request.POST.get('description')
        
        category = get_object_or_404(Category, id=category)
        brand = get_object_or_404(Brand, id=brand)
        # Create Product
        product = Product.objects.create(
            name=name,
            brand=brand,
            description=description,
            category=category,
        )


        return redirect('adminProducts')

    return render(request, 'addProducts.html', {'categories': categories,'brands':brands})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Variant, Size, ProductImage

def addVariant(request):
    products = Product.objects.filter(is_active=True)
    if request.method == 'POST':
        product_id = request.POST.get('product')
        color = request.POST.get('color')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        discount_price = request.POST.get('discount_price')
        sizes = request.POST.getlist('sizes')
        images = request.FILES.getlist('images')

        # Fetch the product instance
        product = get_object_or_404(Product, id=product_id)

        # Create the variant
        variant = Variant.objects.create(
            product=product,
            color=color,
            price=price,
            stock=stock,
            discount_price=discount_price
        )

        # Add sizes to the variant
        for size in sizes:
            Size.objects.create(product_variant=variant, name=size)

        # Add images to the variant
        for index, image in enumerate(images):
            ProductImage.objects.create(
                variant=variant,
                image=image,
                is_primary=(index == 0)  # Set the first image as the primary image
            )

        return redirect('adminProducts')  # Adjust the redirect as needed

    return render(request, 'addVariant.html', {'products': products})


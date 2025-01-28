from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate,logout as auth_logout
from django.contrib import messages
from django.utils.timezone import now
from manager.forms import SignupForm, OTPVerificationForm, PasswordResetRequestForm,SetPasswordForm
from .forms import AddressForm
from manager.models import OTP,User,Category, Brand, Size, Product, Variant, ProductImage, Review, Address, Cart, CartItem, Wishlist,PaymentMethod
from datetime import timezone
from django.views.decorators.cache import never_cache
from django.http import  JsonResponse
import json
from django.conf import settings
from django.apps import apps
from .utils import send_otp_email
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
import logging
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.db import transaction


User = get_user_model()


def home(request):
    products = (
        Product.objects.filter(is_active=True)
        .prefetch_related('variants', 'variants__images')
        .select_related('category', 'brand')
    )[:10]  

    product_data = []
    for product in products:
        primary_variant = product.variants.first()
        if primary_variant:
            primary_image = primary_variant.images.filter(is_primary=True).first()
            product_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': primary_variant.discount_price or primary_variant.price,
                'image_url': primary_image.image.url if primary_image else 'default_image.jpg',
            })

    return render(request, 'home.html', {'products': product_data})



def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            signup_data = form.cleaned_data
            request.session['signup_data'] = signup_data

            otp_instance, created = OTP.objects.get_or_create(email=signup_data['email'])
            otp_instance.generate_otp()
            otp_instance.save()
            print(otp_instance.otp)  # Remove this in production
            try:
                send_otp_email(signup_data['email'], otp_instance.otp, purpose="signup")
                request.session['otp_timer_start'] = now().timestamp()
                
                messages.success(request, "Please verify your email with the OTP.")
                print("signup_data......",signup_data)
                return redirect('verify_otp')
            except Exception as e:
                messages.error(request, f"Failed to send OTP. Please try again. Error: {str(e)}")
                return redirect('signup')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form})





def verify_otp(request):
    print("verify_otp.......//")
    signup_data = request.session.get('signup_data')
    print("signup_data",signup_data)
    if not signup_data:
        messages.error(request, 'Session expired or invalid. Please sign up again.')
        return redirect('signup')
    if request.method == 'POST':
        
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            try:
                otp_instance = OTP.objects.get(email=signup_data['email'])
                
                if not otp_instance.is_valid():
                    messages.error(request, 'OTP has expired. Please request a new one.')
                    return render(request, 'verify_otp.html', {'form': form, 'time_remaining': 0})

                if otp_instance.otp != entered_otp:
                    messages.error(request, 'Invalid OTP. Please try again.')
                    time_remaining = max(0, int((otp_instance.expiration_time - timezone.now()).total_seconds()))
                    return render(request, 'verify_otp.html', {'form': form, 'time_remaining': time_remaining})

                try:
                    print("inside try")
                    print("signup_data['email']",signup_data['email'])
                    # username = signup_data['email'].split('@')[0]
                    user = User.objects.create_user(
                        username=signup_data['first_name'],
                        email=signup_data['email'],
                        phone=signup_data['phone'],
                        password=signup_data['password1'],
                        first_name=signup_data.get('first_name', ''),
                        last_name=signup_data.get('last_name', ''),
                    )
                    print("user is created")
                    print("the user.......",user)
                    
                    request.session.pop('signup_data', None)
                    otp_instance.delete()

                    messages.success(request, 'Account created successfully! Please log in.')
                    return redirect('home')

                except Exception as e:
                    messages.error(request, f'Error creating account: {str(e)}')
                    return redirect('signup')

            except OTP.DoesNotExist:
                messages.error(request, 'Invalid session. Please try again.')
                return redirect('signup')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = OTPVerificationForm()

    try:
        otp_instance = OTP.objects.get(email=signup_data['email'])
        time_remaining = max(0, int((otp_instance.expiration_time - timezone.now()).total_seconds()))
    except OTP.DoesNotExist:
        time_remaining = 0

    return render(request, 'verify_otp.html', {'form': form, 'time_remaining': time_remaining})



# def send_otp_email(email, otp):
#     subject = "Your OTP for Signup"
#     message = f"Your OTP is {otp}. It is valid for 10 minutes."
#     # Implement your email sending logic here
#     print(f"Sending OTP email to {email}: {message}")  # For development purposes

@require_http_methods(["POST"])
def resend_otp(request):
    signup_data = request.session.get('signup_data')
    if not signup_data:
        return JsonResponse({'success': False, 'message': 'Invalid session. Please sign up again.'})

    try:
        otp_instance = OTP.objects.get(email=signup_data['email'])
        
        
        if timezone.now() < otp_instance.created_at + timezone.timedelta(seconds=60):
            time_to_wait = 60 - int((timezone.now() - otp_instance.created_at).total_seconds())
            return JsonResponse({'success': False, 'message': f'Please wait {time_to_wait} seconds before requesting a new OTP.'})

        otp_instance.generate_otp()
        otp_instance.save()

        try:
            send_otp_email(signup_data['email'], otp_instance.otp)
            return JsonResponse({'success': True, 'message': 'A new OTP has been sent to your email.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
    
    except OTP.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Unable to process your request. Please try signing up again.'})






@csrf_exempt
def login(request):
    if request.session.get('signup_success'):
        messages.success(request, "Your account was created successfully! Please log in.")
        del request.session['signup_success']
        print("signup_success")  
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'login.html')

    if request.user.is_authenticated:
        return redirect('home')
    
    return render(request, 'login.html')

from django.urls import reverse   

def profile(request):
    user = request.user

    if request.method == 'POST':
        # Parse the incoming JSON data
        data = json.loads(request.body)
        full_name = data.get('full_name', user.first_name)
        phone = data.get('phone', user.phone)  
        # Update the user model
        user.first_name = full_name
        user.phone = phone 
        user.save()
    

        return JsonResponse({'message': 'Profile updated successfully!'})

    # GET request: Render the profile template
    context = {
        'user': user,
        'user_id': user.id,
        'full_name': user.first_name,
        'email': user.email,
        'phone': user.phone,  
        'referral_code': user.referral_code,  
    }
    return render(request, 'profile.html', context)




# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     if created:
#         User.objects.create(user=instance)
#     else:
#         instance.User.save()



@csrf_exempt  # For simplicity; use CSRF token in production
def auth_receiver(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        credential = data.get('credential')

        if not credential:
            return JsonResponse({'error': 'No credential provided'}, status=400)

        # Verify token with Google
        CLIENT_ID = settings.GOOGLE_OAUTH_CLIENT_ID
        try:
            id_info = id_token.verify_oauth2_token(
                credential,
                requests.Request(),
                CLIENT_ID
            )

            # Extract user info
            email = id_info.get('email')
            first_name = id_info.get('given_name', '')
            last_name = id_info.get('family_name', '')

            # Retrieve or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': email.split('@')[0], 'first_name': first_name, 'last_name': last_name}
            )

            # Log the user in
            auth_login(request, user)
            return JsonResponse({'success': True, 'redirect_url': '/store/home/'})

        except ValueError as e:
            print(f"Token verification error: {str(e)}")
            return JsonResponse({'error': 'Invalid token', 'details': str(e)}, status=400)

    except Exception as e:
        import traceback
        print(f"Error in auth_receiver: {traceback.format_exc()}")
        return JsonResponse({'error': 'Authentication failed'}, status=400)



def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, "No account found with this email.")
                return render(request, 'forgot_password.html')
            
            otp_instance, created = OTP.objects.get_or_create(email=email)
            otp_instance.generate_otp()
            print(otp_instance.otp)
            
            try:
                send_otp_email(email, otp_instance.otp, purpose="reset")
                request.session['reset_email'] = email
                messages.success(request, "OTP sent to your email.")
                return redirect('reset_password')
            except Exception as e:
                messages.error(request, "Failed to send OTP email. Please try again.")
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.")
            
    return render(request, 'forgot_password.html')

def reset_password(request):
    reset_email = request.session.get('reset_email')
    if not reset_email:
        messages.error(request, "Please submit your email first.")
        return redirect('forgot_password')

    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        otp = request.POST.get('otp')
        
        try:
            otp_instance = OTP.objects.get(email=reset_email)
            if otp_instance.is_valid() and otp_instance.otp == otp:
                if form.is_valid():
                    user = User.objects.get(email=reset_email)
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    del request.session['reset_email']
                    messages.success(request, "Password has been reset successfully!")
                    return redirect('login')
            else:
                messages.error(request, "Invalid or expired OTP.")
        except (OTP.DoesNotExist, User.DoesNotExist):
            messages.error(request, "Invalid reset attempt.")
    else:
        form = SetPasswordForm()
    
    return render(request, 'reset_password.html', {'form': form})


def logout(request):
    
    auth_logout(request)
    
    return redirect('signup')


def get_variant_data(request, product_id, variant_id):
    variant = get_object_or_404(
        Variant.objects.filter(product_id=product_id, id=variant_id)
        .prefetch_related('sizes', 'images')
    )
    
    data = {
        'id': variant.id,
        'price': float(variant.price),
        'discount_price': float(variant.discount_price) if variant.discount_price else None,
        'stock': variant.stock,
        'sizes': list(variant.sizes.values('id', 'name')),
        'images': list(variant.images.values('id', 'image', 'is_primary'))
    }
    
    return JsonResponse(data)

def product_list(request):
    products = (
        Product.objects.filter(is_active=True)
        .prefetch_related('variants', 'variants__images')
        .select_related('category', 'brand')
    )

    product_data = []
    for product in products:
        primary_variant = product.variants.first()
        if primary_variant:
            primary_image = primary_variant.images.filter(is_primary=True).first()
            product_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': primary_variant.discount_price or primary_variant.price,
                'image_url': primary_image.image.url if primary_image else 'default_image.jpg',
            })

    paginator = Paginator(product_data, 12)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.all()

    context = {
        'products': page_obj,
        'categories': categories,
        'brands': brands,
    }

    return render(request, 'product_list.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand')
        .prefetch_related(
            'variants',
            'variants__sizes',
            'variants__images'
        ),
        id=product_id,
        is_active=True
    )
    
    variants = list(product.variants.all())
    primary_variant = variants[0] if variants else None
    
    colors = list(set(variant.color for variant in variants if variant.color))
    sizes = list(primary_variant.sizes.all()) if primary_variant else []

    # Assuming avg_rating, rating_count, reviews, and breadcrumb are defined elsewhere and passed to this function.  Replace with your actual logic to fetch these values.
    avg_rating = 4.5  # Placeholder
    rating_count = 10 # Placeholder
    reviews = [] # Placeholder
    breadcrumb = ["Home", "Category", product.name] # Placeholder


    context = {
        'product': product,
        'brand': product.brand.name, 
        'primary_variant': primary_variant,
        'variants': variants,
        'colors': [{'id': v.id, 'color': v.color} for v in variants],
        'sizes': sizes,
        'avg_rating': round(avg_rating, 1),
        'rating_count': rating_count,
        'reviews': reviews,
        'breadcrumb': breadcrumb,
    }
    
    return render(request, 'product_details.html', context)

######### CART #########

from django.contrib.auth.decorators import login_required
from django.db import transaction
from manager.models import Cart, CartItem, Variant, Size, Wishlist

# In your app's views.py file
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from manager.models import Variant, CartItem, Cart

def view_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            user=request.user,
            is_ordered=False
        )
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    
    # Ensure cart items are properly prefetched
    cart_items = cart.items.select_related('variant', 'size').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': cart.total_price,
        'total_discount': cart.total_discount,
        'final_price': cart.final_price
    }
    
    return render(request, 'cart.html', context)


logger = logging.getLogger(__name__)

@require_POST
@csrf_exempt
def add_to_cart(request):
    try:
        # data = json.loads(request.body)
        # variant_id = data.get('variant_id')
        # quantity = int(data.get('quantity', 1))

        if request.method == 'POST':

            try:
                data = json.loads(request.body)
                variant_id = data.get('variant_id')
                quantity = int(data.get('quantity', 1))
                variant = Variant.objects.get(id=variant_id)
                size = data.get('size')
            except Variant.DoesNotExist:
                logger.error(f"Variant with id {variant_id} not found")
                return JsonResponse({'success': False, 'message': 'Product variant not found'}, status=404)

            if variant.stock < quantity:
                return JsonResponse({'success': False, 'message': 'Not enough stock available'}, status=400)

            with transaction.atomic():
                # Get or create the user's cart
                if request.user.is_authenticated:
                    cart, created = Cart.objects.get_or_create(user=request.user, is_ordered=False)
                else:
                    cart_id = request.session.get('cart_id')
                    if cart_id:
                        try:
                            cart = Cart.objects.get(id=cart_id)
                        except Cart.DoesNotExist:
                            cart = Cart.objects.create()
                            request.session['cart_id'] = cart.id
                    else:
                        cart = Cart.objects.create()
                        request.session['cart_id'] = cart.id

                # Check if the item is already in the cart
                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=cart,
                    variant=variant,
                    defaults={'quantity': 0}
                )

                # Update the quantity
                cart_item.quantity += quantity
                cart_item.save()

                # Update the stock
                variant.stock -= quantity
                variant.save()

            # Get the updated cart count
            cart_count = sum(item.quantity for item in cart.items.all())

            return JsonResponse({
                'success': True,
                'message': 'Item added to cart successfully',
                'cart_count': cart_count
            })

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({'success': False, 'message': 'Invalid request data'}, status=400)
    except Exception as e:
        logger.error(f"Error in add_to_cart: {str(e)}")
        return JsonResponse({'success': False, 'message': 'An error occurred while processing your request'}, status=500)

@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def move_to_wishlist(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        # Add to wishlist
        Wishlist.objects.get_or_create(
            user=request.user,
            variant=cart_item.variant
        )
        
        # Remove from cart
        cart_item.delete()
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

####### profile ##########

def user_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    context = {
        'full_name': user.get_full_name(),
        'email': user.email,
        'phone': user.phone if hasattr(user, 'profile') else 'N/A',  # Check if user has a profile
        'referral_code': user.referral_code if hasattr(user, 'profile') else 'N/A',
    }
    return render(request, 'profile.html', context)


################## Addresss ####################


@never_cache
@login_required(login_url='userlogin')
def userManageAddress(request):
    user_addresses = Address.objects.filter(user=request.user, is_deleted=False)
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # Handle default address setting
            if address.is_default:
                with transaction.atomic():
                    Address.objects.filter(user=request.user).update(is_default=False)
            
            address.save()
            return JsonResponse({'success': True, 'message': 'Address added successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Error in adding address', 'errors': form.errors})

    context = {
        'addresses': user_addresses,
    }
    return render(request, 'usermanageaddress.html', context)

@login_required(login_url='userlogin')
@never_cache
def editAddress(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user, is_deleted=False)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            
            # Handle default address setting
            if address.is_default:
                with transaction.atomic():
                    Address.objects.filter(user=request.user).exclude(id=address_id).update(is_default=False)
            
            address.save()
            return redirect('userManageAddress')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'usereditaddress.html', {'form': form, 'address': address})

@login_required(login_url='userlogin')
@never_cache
def deleteAddress(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_deleted = True
    address.save()
    return JsonResponse({'success': True, 'message': 'Address deleted successfully'})

@login_required(login_url='userlogin')
@csrf_exempt
def set_primary_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            address_id = data.get('address_id')
            
            with transaction.atomic():
                # First, unset all default addresses
                Address.objects.filter(user=request.user).update(is_default=False)
                # Then set the selected address as default
                address = Address.objects.get(id=address_id, user=request.user)
                address.is_default = True
                address.save()
            
            return JsonResponse({'success': True})
        except Address.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Address not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)



################ checout #####################

@login_required(login_url='userlogin')
@never_cache
def user_checkout(request):
    #removing the invalid cart iems beforeproceeding to checkout
    CartItem.objects.filter(variant__isnull=True).delete()

    # Fetch user addresses
    user_addresses = Address.objects.filter(user=request.user, is_deleted=False)
    payment_methods = PaymentMethod.objects.all()
    

    try:
        # Fetch the cart for the current user
        cart, _ = Cart.objects.get_or_create(user=request.user, is_ordered=False)
        cart_items = cart.items.select_related('variant__product', 'size').all()

        # Initialize variables
        total_quantity = 0
        cart_items_with_prices = []
        out_of_stock_items = []

        for item in cart_items:
            # Skip items with no variant
            if not item.variant:
                messages.warning(
                    request,
                    f"One of your cart items is invalid and has been removed."
                )
                item.delete()  # Remove invalid items from the cart
                continue

            # Process valid items
            total_quantity += item.quantity
            total_price = item.subtotal  # Use the `subtotal` property
            cart_items_with_prices.append({
                'item': item,
                'total_price': total_price,
            })

            # Check stock
            if item.quantity > item.variant.stock:
                out_of_stock_items.append(item)

        # Handle out-of-stock items
        if out_of_stock_items:
            messages.warning(
                request,
                "Some items in your cart have insufficient stock. Please update your cart."
            )
            return redirect('view_cart')

    except Cart.DoesNotExist:
        cart = None
        cart_items_with_prices = []
        total_quantity = 0

    # Prepare context for the template
    context = {
        'user_addresses': user_addresses,
        'cart_items_with_prices': cart_items_with_prices,
        'cart': cart,
        'total_price': cart.total_price if cart else 0,  # Use the `Cart` model's property
        'total_discount': cart.total_discount if cart else 0,
        'final_total_price': cart.final_price if cart else 0,
        'payment_methods': payment_methods,
        'total_quantity': total_quantity,
    }

    return render(request, 'checkout.html', context)









################# Order ####################
from manager.models import Order, OrderItem, Cart, CartItem
 

@login_required(login_url='userlogin')
def place_order(request):
    if request.method == 'POST':
        try:
            # Extract data from request.POST
            address_id = request.POST.get('address_id')
            payment_method = request.POST.get('payment_method')

            # Fetch the selected address from the database
            selected_address = Address.objects.get(id=address_id, user=request.user)

            # Manually populate the AddressForm with the selected address data
            address_data = {
                'address_type': selected_address.address_type,
                'full_name': selected_address.full_name,
                'phone': selected_address.phone,
                'pincode': selected_address.pincode,
                'address_line1': selected_address.address_line1,
                'address_line2': selected_address.address_line2,
                'landmark': selected_address.landmark,
                'city': selected_address.city,
                'state': selected_address.state,
                'is_default': selected_address.is_default,
            }

            address_form = AddressForm(address_data)

            if address_form.is_valid():
                with transaction.atomic():
                    # Get or create the user's cart
                    cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)

                    # Check if cart is empty
                    if not cart.items.exists():
                        return JsonResponse({'success': False, 'message': 'Your cart is empty. Please add items before placing an order.'}, status=400)

                    # Create a new order
                    order = Order.objects.create(
                        user=request.user,
                        total_amount=cart.total_price,
                        paymentmethod_id=payment_method,
                        total_discount=cart.total_discount,
                        payment_status='PENDING',
                        order_status='PROCESSING'
                    )

                    # Save the address
                    address = address_form.save(commit=False)
                    address.user = request.user
                    address.save()
                    order.address = address
                    order.save()

                    # Create order items from cart items
                    for cart_item in cart.items.all():
                        OrderItem.objects.create(
                            order=order,
                            product=cart_item.product,
                            variant=cart_item.variant,
                            quantity=cart_item.quantity,
                            price=cart_item.variant.price,
                            status='Processing'
                        )

                        # Reduce stock
                        if cart_item.variant:
                            cart_item.variant.stock -= cart_item.quantity
                            cart_item.variant.save()
                        else:
                            cart_item.product.stock -= cart_item.quantity
                            cart_item.product.save()

                    # Clear the cart
                    cart.items.all().delete()
                    cart.is_active = False
                    cart.save()

                    return JsonResponse({
                        'success': True,
                        'redirect_url': reverse('order_confirmation', args=[order.id])
                    })
            else:
                return JsonResponse({'success': False, 'message': 'Invalid address data', 'errors': address_form.errors}, status=400)

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred while placing your order: {str(e)}'}, status=500)

    else:
        address_form = AddressForm()

    # Get or create the user's cart
    cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)
    cart_items = cart.items.all()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'address_form': address_form,
    }
    return render(request, 'place_order.html', context)

@login_required(login_url='userlogin')
def order_confirmation(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('my_orders')
    
    context = {
        'order': order,
    }
    return render(request, 'order_confirmation.html', context)
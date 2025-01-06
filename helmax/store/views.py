from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate,logout as auth_logout
from django.contrib import messages
from django.utils.timezone import now
from manager.forms import SignupForm, OTPVerificationForm, PasswordResetRequestForm,SetPasswordForm
from manager.models import OTP,User,Category, Brand, Size
from datetime import timezone
from django.views.decorators.cache import never_cache
from django.http import  JsonResponse

from django.conf import settings
from django.apps import apps
from .utils import send_otp_email
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests
from django.views.decorators.http import require_http_methods




# # Get the custom User model and OTP model
# User = apps.get_model('manager', 'User')
# OTP = apps.get_model('manager', 'OTP')

# Home View
def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            signup_data = form.cleaned_data
            request.session['signup_data'] = signup_data

            # Generate and send OTP
            otp_instance, created = OTP.objects.get_or_create(email=signup_data['email'])
            otp_instance.generate_otp()
            print(otp_instance.otp)
            try:
                send_otp_email(signup_data['email'], otp_instance.otp, purpose="signup")
                request.session['otp_timer_start'] = now().timestamp()
                messages.success(request, "Please verify your email with the OTP.")
                return redirect('verify_otp')
            except Exception as e:
                messages.error(request, "Failed to send OTP. Please try again.")
                return redirect('signup')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form})





def verify_otp(request):
    signup_data = request.session.get('signup_data')
    if not signup_data:
        messages.error(request, 'Invalid session. Please sign up again.')
        return redirect('signup')

    timer_start = request.session.get('otp_timer_start')
    if not timer_start:
        messages.error(request, 'Please request an OTP first.')
        return redirect('signup')

    current_time = now().timestamp()  
    elapsed_time = int(current_time - float(timer_start))
    time_remaining = max(0, 60 - elapsed_time)

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            try:
                otp_instance = OTP.objects.get(email=signup_data['email'])
                
                # Check OTP validity
                if not otp_instance.is_valid():
                    messages.error(request, 'OTP has expired. Please request a new one.')
                    return render(request, 'verify_otp.html')

                if otp_instance.otp != entered_otp:
                    messages.error(request, 'Invalid OTP. Please try again.')
                    return render(request, 'verify_otp.html', {'form': form, 'time_remaining': max(0, int(time_remaining))})

                # OTP is valid, create user
                try:
                    username = signup_data['email'].split('@')[0]
                    user = User.objects.create_user(
                        username=username,
                        email=signup_data['email'],
                        password=signup_data['password1'],
                        first_name=signup_data.get('first_name', ''),
                        last_name=signup_data.get('last_name', ''),
                        phone=signup_data.get('phone', '')
                    )

                    # Clean up session and OTP data
                    request.session.pop('signup_data', None)
                    request.session.pop('otp_timer_start', None)
                    otp_instance.delete()

                    messages.success(request, 'Account created successfully! Please log in.')
                    return redirect('login')

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

    return render(request, 'verify_otp.html', {'form': form, 'time_remaining': max(0, int(time_remaining))})



# def resend_otp(request):
#     if request.method == 'POST':
#         signup_data = request.session.get('signup_data')
#         if not signup_data:
#             return JsonResponse({'success': False, 'message': 'Session expired. Please sign up again.'}, status=400)

#         try:
#             otp_instance, created = OTP.objects.get_or_create(email=signup_data['email'])
#             otp_instance.generate_otp()  # Generate a new OTP
#             request.session['otp_timer_start'] = now().timestamp()  # Reset timer

#             # Simulate sending the OTP (e.g., via email or SMS)
#             print(f"New OTP for {signup_data['email']}: {otp_instance.otp}")

#             return JsonResponse({'success': True, 'message': 'OTP has been resent successfully.'})

#         except Exception as e:
#             return JsonResponse({'success': False, 'message': str(e)}, status=500)

#     return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

# Helper function to send OTP email
def send_otp_email(email, otp, purpose="signup"):
    subject = "Your OTP for Signup"
    message = f"Your OTP is {otp}. It is valid for 1 minutes."
    # Implement your email sending logic here
    print(f"Sending OTP email to {email}: {message}")  # For development purposes



def resend_otp(request):
    signup_data = request.session.get('signup_data')
    if not signup_data:
        messages.error(request, 'Invalid session. Please sign up again.')
        return redirect('signup')

    timer_start = request.session.get('otp_timer_start')
    if timer_start:
        elapsed_time = int(now().timestamp() - float(timer_start))
        if elapsed_time < 60:
            messages.error(request, f'please wait {60 - elapsed_time} seconds before resending OTP.')
            return redirect('verify_otp')
    
    try:
        otp_instance, created = OTP.objects.get_or_create(email=signup_data['email'])
        otp_instance.generate_otp()
        print(otp_instance.otp) 


        try:
            send_otp_email(signup_data['email'], otp_instance.otp, purpose="signup")
            request.session['otp_timer_start'] = now().timestamp()
            messages.success(request, 'A new OTP has been sent to your email.')
        except Exception as e:
            messages.error(request, 'Failed to send OTP. Please try again.')
    
    except OTP.DoesNotExist:
        messages.error(request, 'Unable to process your request. Please try siging up again.')

    return redirect('verify_otp')


@csrf_exempt
def login(request):
    if request.session.get('signup_success'):
        messages.success(request, "Your account was created successfully! Please log in.")
        del request.session['signup_success']  # Clear the flag after showing the message

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

    

@csrf_exempt
def auth_receiver(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    try:
        # Parse JSON data from request body
        import json
        data = json.loads(request.body)
        credential = data.get('credential')
        
        if not credential:
            return JsonResponse({'error': 'No credential provided'}, status=400)

        # Get client ID from settings
        CLIENT_ID = settings.GOOGLE_OAUTH_CLIENT_ID
        
        try:
            id_info = id_token.verify_oauth2_token(
                credential,
                requests.Request(),
                CLIENT_ID
            )

            # Get user info from the token
            email = id_info.get('email')
            first_name = id_info.get('given_name', '')
            last_name = id_info.get('family_name', '')

            # Check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create new user if doesn't exist
                username = email.split('@')[0]
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )

            # Log the user in
            auth_login(request, user)
            return JsonResponse({
                'success': True,
                'redirect_url': '/store/home/'
            })

        except ValueError as e:
            print(f"Token verification error: {str(e)}")
            return JsonResponse({'error': 'Invalid token'}, status=400)

    except Exception as e:
        print(f"Error in auth_receiver: {str(e)}")
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

















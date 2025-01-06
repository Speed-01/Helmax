from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(email, otp, purpose="signup"):
    """
    Send OTP email for signup or password reset
    """
    if purpose == "signup":
        subject = "Your OTP for Signup in Helmax"
        message = f"Your OTP is {otp}. It is valid for 2 minutes."
    else:  # password reset
        subject = "Password Reset OTP"
        message = f"Your OTP for password reset is {otp}. Valid for 2 minutes."

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
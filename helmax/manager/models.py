from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.timezone import now
from cloudinary.models import CloudinaryField
import datetime
from datetime import timedelta







from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now



class library(models.Model):
  
  
  image = CloudinaryField('image')

class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(default=None)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    referral_code = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return self.username




class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    expiration_time = models.DateTimeField(null=True)

    def generate_otp(self):
        # Generate OTP logic here
        import random
        self.otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Set expiration time to 10 minutes from creation
        self.expiration_time = timezone.now() + timedelta(minutes=10)
        self.save()

    def is_valid(self):
        # OTP is valid for 2 minutes
        expiry_time = self.created_at + timezone.timedelta(minutes=1)
        return timezone.now() <= expiry_time

    
class BaseModel(models.Model):
    
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True



class Category(BaseModel):
    name = models.CharField(max_length=100,unique=True)
    is_deleted = models.BooleanField(default=False) 

    def __str__(self):
        return self.name

    

class Brand(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

from django.db import models
from django.core.exceptions import ValidationError






class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products',null=True, blank=True)
    is_active = models.BooleanField(default=True)  # Added field for activation

    def __str__(self):
        return self.name


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.color}"
    
class Size(models.Model):
    SIZE_CHIOCES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    )
    name = models.CharField(max_length=10, choices=SIZE_CHIOCES)
    product_variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='sizes')

    def __str__(self):
        return f"{self.product_variant} - {self.name}"


class ProductImage(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='images')  # Removed default
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.variant}"
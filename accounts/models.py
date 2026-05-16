import random
import string
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


def generate_account_number():
    """Generate unique 12-digit account number."""
    prefix = 'NP'
    digits = ''.join(random.choices(string.digits, k=10))
    return f"{prefix}{digits}"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    account_number = models.CharField(max_length=20, unique=True, blank=True)
    pin = models.CharField(max_length=128)          # stored hashed
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.account_number:
            acc = generate_account_number()
            while User.objects.filter(account_number=acc).exists():
                acc = generate_account_number()
            self.account_number = acc
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.account_number})"


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        from django.conf import settings
        from datetime import timedelta
        expiry = self.created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        return timezone.now() > expiry

    def __str__(self):
        return f"OTP for {self.user.email}"

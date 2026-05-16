import random
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(user):
    """Generate OTP, save it, and send via Gmail SMTP."""
    # Invalidate old OTPs
    OTP.objects.filter(user=user, is_used=False).update(is_used=True)

    code = generate_otp()
    OTP.objects.create(user=user, code=code)

    subject = "NovaPay – Your Verification Code"
    message = f"""
Hello {user.full_name},

Your NovaPay verification code is:

    {code}

This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.
Do not share this code with anyone.

– The NovaPay Team
    """
    html_message = f"""
<div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;background:#0a1628;color:#e8f0fe;border-radius:16px;">
  <h2 style="color:#00d4aa;margin-bottom:8px;">NovaPay</h2>
  <p style="color:#8ba3c7;">Hello {user.full_name},</p>
  <p style="color:#8ba3c7;">Your verification code is:</p>
  <div style="font-size:40px;font-weight:700;letter-spacing:12px;text-align:center;padding:24px;background:#162843;border-radius:12px;color:#ffffff;margin:16px 0;">
    {code}
  </div>
  <p style="color:#8ba3c7;font-size:13px;">Expires in <strong>{settings.OTP_EXPIRY_MINUTES} minutes</strong>. Never share this code.</p>
</div>
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    return code


def verify_otp_code(user, code):
    """Returns True if OTP is valid, False otherwise."""
    otp = OTP.objects.filter(
        user=user,
        code=code,
        is_used=False
    ).order_by('-created_at').first()

    if not otp:
        return False, "Invalid OTP."
    if otp.is_expired():
        return False, "OTP has expired. Please request a new one."

    otp.is_used = True
    otp.save()
    return True, "OTP verified."

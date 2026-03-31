import random
from django.core.mail import send_mail
from django.conf import settings


def generate_verification_code():
    return str(random.randint(100000, 999999))


def send_verification_email(user, code, override_email=None):
    recipient = override_email if override_email else user.email

    subject = "Verify your Helping Connections account"
    message = (
        f"Hi {user.username},\n\n"
        f"Your verification code is: {code}\n\n"
        f"This code expires in 10 minutes.\n\n"
        f"If you did not create this account, you can ignore this email."
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )

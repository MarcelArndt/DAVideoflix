from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from auth_app.models import Profiles
from django.db.models.signals import post_save
from django.conf import settings
import django_rq
import os
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from dotenv import load_dotenv
load_dotenv()


'''
After creating a new account, it will send an email to the user with a link to activate their account.
'''
@receiver(post_save, sender=Profiles)
def send_verification_email(sender, instance, created, **kwargs):

    queue = django_rq.get_queue('default', autocommit=True)
    queue.enqueue(sendMail,created, instance)


def sendMail(created, instance):
    if created:
        if not instance.is_superuser:
            instance.is_active = False
            instance.save()
        subject = "Willkommen bei Videoflix"
        from_email = os.environ.get("DEFAULT_FROM_EMAIL", default="noreply@videoflix.de")
        basis_url_frontend = os.environ.get("BASIS_URL_FRONTEND", default="http://localhost:5500")
        uidb64Id =  urlsafe_base64_encode(force_bytes(instance.pk))

        context = {
            "username": instance.username,
            "verify_link": f"{basis_url_frontend}/pages/auth/activate.html?uid={uidb64Id}&token={instance.email_token}"
        }
        html_content = render_to_string("emails/verification_email.html", context)
        email = EmailMultiAlternatives(subject, "", from_email, [instance.email])
        email.attach_alternative(html_content, "text/html")
        email.send()
        
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
User = get_user_model()

from dotenv import load_dotenv
import os
load_dotenv()

def send_validation_email(profil_id):
    user = User.objects.get(id = profil_id)
    subject = "Willkommen bei Videoflix"
    from_email = os.environ.get("DEFAULT_FROM_EMAIL", default="noreply@utils.de")
    basis_url_backend = os.environ.get("BASIS_URL_BACKEND", default="http://localhost:8000")
    context = {
        "username": user.user.username,
        "verify_link": f"{basis_url_backend}/api/verify-email/?token={user.email_token}"
    }
    html_content = render_to_string("emails/verification_email.html", context)
    email = EmailMultiAlternatives(subject, "", from_email, [user.user.email])
    email.attach_alternative(html_content, "text/html")
    email.send()
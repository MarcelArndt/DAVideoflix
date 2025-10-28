import os
from rest_framework import serializers

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from auth_app.models import Profiles

from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.conf import settings

from django.utils.http import urlsafe_base64_decode

from dotenv import load_dotenv

import secrets

load_dotenv()

User = get_user_model()

'''
Validates the provided email and password fields, ensures that the
passwords match, and that the email address is unique. Upon successful
validation, it creates a new `Profiles` user instance with a unique
username and an email verification token.
'''
class RegestrationSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only = True)
    password = serializers.CharField(write_only = True)
    email = serializers.EmailField(write_only=True)

    class Meta():
        model = Profiles
        fields = ["email", "password", "confirmed_password"]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        password = data.get("password")
        confirmed_password = data.get("confirmed_password")
        email = data.get("email")

        if not confirmed_password == password:
            raise serializers.ValidationError({'Error':"passwords doesn't match"})
        if not email:
            raise serializers.ValidationError({'Error':"Email is required."})
        if Profiles.objects.filter(email = email).exists():
            raise serializers.ValidationError({'Error':"Email already exists."}) 
        return data

    def create(self, validated_data) :
        password = self.validated_data.get('password')
        email = self.validated_data.get("email")
        token = secrets.token_urlsafe(32)
        base_username = email.split("@")[0]
        new_username = base_username
        counter = 1
        while Profiles.objects.filter(username=new_username).exists():
            new_username = f"{base_username}{counter}"
            counter += 1
        profil = Profiles.objects.create_user(username = new_username, email = email, password = password, email_token = token )
        return profil
    

'''
Login
Custom JWT authentication serializer that uses email instead of username.
This serializer validates a user's email and password combination.
If valid, it generates and returns a JWT access/refresh token pair along
with additional user information.
'''
class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if 'username' in self.fields:
            self.fields.pop('username')

    def validate(self, data):
            email = data.get("email")
            password = data.get("password")
            user = None
            try:
                user = Profiles.objects.get(email=email)
            except Profiles.DoesNotExist:
                raise serializers.ValidationError({"message": "wrong email or password"})

            if not user.check_password(password):
                raise serializers.ValidationError({"message": "wrong email or password"})

            data = super().validate({
                'username': user.username, 
                'password': password
            })

            data.update({
                'user_id': user.id,
                'email': user.email,
            })

            return data


'''
Serializer for sending a password reset email.
Validates that the provided email belongs to a registered user.
Generates a secure password reset token and UID, constructs a reset
link, and sends an email to the user with instructions to reset
their password.
'''      
class SendEmailForResetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        try:
            user = Profiles.objects.get(email=email)
        except:
             raise serializers.ValidationError({'Message':"No User found"})
        userId = urlsafe_base64_encode(force_bytes(user.pk))
        token  = default_token_generator.make_token(user)
        username = user.username
        user_email = user.email
        base_url_frontend = os.environ.get('BASIS_URL_FRONTEND', default="http://127.0.0.1:5500")
        reset_link = f'{base_url_frontend}/pages/auth/confirm_password.html?uid={userId}&token={token}'
        self.send_email_to_user(username, user_email, reset_link)
        return {"detail":'An email has been sent to reset your password.'}



    def send_email_to_user(self, username, user_email, reset_link):
        html_content = render_to_string("emails/reset-password.html", {
            "username": username,
            "reset_link": reset_link,
        })
        text_content = f"Klicke hier, um dein Passwort zurückzusetzen:\n{reset_link}"
        email = EmailMultiAlternatives(
            subject="Reset your Password",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

'''
Serializer for resetting a user's password.
Validates the provided new password and confirmation password,
checks the UID and token from the request query parameters,
and updates the user's password if everything is valid.
'''    
class ResetPasswordSerializer(serializers.Serializer):
    new_password= serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)


    def validate(self, data):
        request = self.context.get("request")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")
        token = request.query_params.get("token")
        uidb64 = request.query_params.get("id")
        userId = urlsafe_base64_decode(uidb64)
        try:
            user = Profiles.objects.get(pk=userId)
        except:
            raise serializers.ValidationError({'message':"No User found"})
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({'message': "Invalid or expired token"})
        if new_password != confirm_password:
             raise serializers.ValidationError({'message':"Passwords not match"})
        user.set_password(new_password)
        user.save()
        return { "detail": "Your Password has been successfully reset."}
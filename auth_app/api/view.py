import os
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model

from auth_app.api.serializers import RegestrationSerializer, SendEmailForResetPasswordSerializer, ResetPasswordSerializer, ResetValidationEmailSerializer, EmailTokenObtainSerializer, UserIsAuthenticadeAndVerified
from auth_app.auth import CookieJWTAuthentication
from auth_app.permissions import AllowAnyButTrackAuth

from rest_framework.views import APIView 
from rest_framework.generics import ListAPIView
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny

from .serializers import UserSerializer
from dotenv import load_dotenv
from django.contrib.auth.tokens import default_token_generator

from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str 

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

load_dotenv()
User = get_user_model()

ISDEBUG = os.environ.get("DEBUG", default="True")
SECURE = False if ISDEBUG == "True" else True
print(SECURE)

class RegestrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []     

    def post(self, request, *args, **kwargs):
        serializer = RegestrationSerializer(data= request.data)
        if serializer.is_valid():
            saved_user = serializer.save()
            data = { "user": {
                "id": saved_user.id,
                "email": saved_user.email,

            },
             "token": saved_user.email_token
            }
        else:
            data = serializer.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_201_CREATED)

    
class CookieTokenLogoutView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []     

    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get('access_key')
        refresh_token = request.COOKIES.get('refresh_key')

        if not access_token or not refresh_token:
            return Response(
                {"detail": "Refresh-Token is missing."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response = Response({"detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."},status=status.HTTP_200_OK)
        expires = datetime.now() - timedelta(days=1)

        response.set_cookie(
            key = 'access_key',
            value = '',
            expires = expires,
            httponly = True,
            secure = SECURE,
            samesite='Lax'
        )

        response.set_cookie(
            key = 'refresh_key',
            value = '',
            httponly = True,
            expires = expires,
            secure = SECURE,
            samesite='Lax'
        )

        return response
    

class CookieTokenObtainView(TokenObtainPairView):

    permission_classes = [AllowAny]
    authentication_classes = []    

    serializer_class = EmailTokenObtainSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            validated = serializer.validated_data
            refresh = serializer.validated_data['refresh']
            access = serializer.validated_data['access']
            expires = datetime.now() + timedelta(days=7)
            response = Response({
                "detail": "Login successful",
                "user": {
                    "id": validated.get('user_id'),
                    "username": validated.get('email')
                }
                },status=status.HTTP_200_OK)

            response.set_cookie(
                key = 'access_key',
                value = str(access),
                httponly = True,
                expires=expires,
                secure = SECURE,
                samesite='Lax'
            )

            response.set_cookie(
                key = 'refresh_key',
                expires=expires,
                value = str(refresh),
                httponly = True,
                secure = SECURE,
                samesite='Lax'
            )

            return response
        return Response({'message':'wrong e-mail or password'},status=status.HTTP_401_UNAUTHORIZED)
    
class CookieTokenRefreshView(TokenRefreshView):

    permission_classes = [AllowAny]
    authentication_classes = []    

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_key')
        if not refresh_token:
            return Response({'message':'Refresh-Token is missing'}, status=status.HTTP_400_BAD_REQUEST)            
        serializer = self.get_serializer(data={'refresh':refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({'message':'Refresh-Token is invalid'},status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get('access')

        response = Response({ "detail": "Token refreshed", "access": access_token},status=status.HTTP_200_OK)
        response.set_cookie(
            key = 'access_key',
            value = str(access_token),
            httponly = True,
            secure = SECURE,
            samesite='Lax'
        )
        return response
    
    
class CookieIsAuthenticatedAndVerifiedView(APIView):

    permission_classes = [AllowAnyButTrackAuth]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        if self.request.user and self.request.user.is_authenticated:
             serializer = UserIsAuthenticadeAndVerified(instance=request.user, context={'request': request})
             return Response({'authenticated': True, 'email_confirmed': request.user.email_is_confirmed, 'message': 'User is authenticated' }, status=status.HTTP_200_OK)
        else:
             return Response({'authenticated': False, 'email_confirmed': None, 'message': 'User is not authenticated' }, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []    

    def get(self, request, uidb64, token):
        id = force_str(urlsafe_base64_decode(uidb64))
        try:
            user = User.objects.get(pk=id)
        except:
            return Response({"message": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        if(user.email_token == token):
            user.email_is_confirmed = True
            user.is_active = True
            user.save()
        else:
            return Response({"message": "Link is invalid"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)

        

class SendEmailForResetPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [] 

    def post(self, request):
        serializer = SendEmailForResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

class SetNewPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []    
    
    def post(self, request, uidb64, token):
        id = force_str(urlsafe_base64_decode(uidb64))
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        try:
            user = User.objects.get(pk=id)
        except:
            return Response({"detail": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return Response({'detail': "Password don't match"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'detail': "Your Password has been successfully reset."}, status=status.HTTP_200_OK)

    
class ResendEmailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        serializer = ResetValidationEmailSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
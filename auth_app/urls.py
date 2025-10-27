from django.urls import path
from .api.view import RegestrationView, VerifyEmailView, SendEmailForResetPasswordView, SetNewPasswordView, ResendEmailView, CookieTokenObtainView, CookieTokenRefreshView, CookieTokenLogoutView, CookieIsAuthenticatedAndVerifiedView

urlpatterns = [
    path("login/", CookieTokenObtainView.as_view(), name='token_obtain_pair'),
    path("register/", RegestrationView.as_view(), name="registration"),
    path('activate/<str:uidb64>/<str:token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('password_reset/', SendEmailForResetPasswordView.as_view(), name='find_user_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', SetNewPasswordView.as_view(), name='password_reset'),
    path('resend-email/', ResendEmailView.as_view(), name='resend-email'),
    path('logout/', CookieTokenLogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('is-authenticated/', CookieIsAuthenticatedAndVerifiedView.as_view(), name='token_is_auth')
]
from django.urls import path, include
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include, re_path
from service_app.api.views import ServeMediaView

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    path('api/admin/', admin.site.urls),      
    path("api/", include('auth_app.urls')),
    path("api/", include('service_app.urls')),
    re_path(r'^media/(?P<path>.*)$', ServeMediaView.as_view(), name='serve_media'),
]


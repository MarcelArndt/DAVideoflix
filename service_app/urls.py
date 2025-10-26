from django.urls import path
from service_app.api.views import VideosListView, ServeVideoMasterView, ServeHlsSegmentView


urlpatterns = [
    path("video/", VideosListView.as_view(), name="media_list"),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', ServeVideoMasterView.as_view(), name='serve_hls_playlist'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>', ServeHlsSegmentView.as_view(), name='serve_hls_segment'),
]
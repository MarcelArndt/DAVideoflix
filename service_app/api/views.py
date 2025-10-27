from rest_framework import generics
from service_app.models import Video,  VideoProgress, CurrentVideoConvertProgress
from rest_framework.views import APIView
from .serializers import VideosSerializer, VideoProgressSerializer, CurrentVideoConvertProgressSerializer, VideoMasterSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.http import FileResponse, Http404
from auth_app.auth import CookieJWTAuthentication
from django.contrib.auth.models import User
from django.conf import settings
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

CACHE_TIMER = int(os.getenv('CACHE_TIMER', default=0))

class VideosListView(APIView):
    authentication_classes = [CookieJWTAuthentication]
        
    def get(self, request):
        cache_key = 'video_list_view'
        cached_response = cache.get(cache_key)

        if cached_response:
            return Response(cached_response)

        videos = Video.objects.all()
        serialized = VideosSerializer(videos, many=True, context={'request': request})
        cache.set(cache_key, serialized.data, timeout=CACHE_TIMER)
        return Response(serialized.data)

class VideosDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideosSerializer

    def perform_destroy(self, instance):
        cache.delete("video_list_view")
        return super().perform_destroy(instance)
    

class ServeVideoMasterView(APIView):
    def get(self, request, movie_id, resolution):
        try:
            video = Video.objects.get(pk=movie_id)
        except Video.DoesNotExist:
            raise Http404("Video not found")
        
        filename, _ = os.path.splitext(os.path.basename(video.url.path))
        filename = filename.replace('_master', '')
        filename = filename[0:20]
        
        playlist_path = os.path.join(
            settings.MEDIA_ROOT,
            'uploads/videos/converted',
            f'{filename}_{resolution}',
            'index.m3u8'
        )
        
        if not os.path.exists(playlist_path):
            raise Http404(f"Playlist not found: {playlist_path}")
        
        return FileResponse(
            open(playlist_path, 'rb'),
            content_type='application/vnd.apple.mpegurl'
        )


class ServeHlsSegmentView(APIView):
    def get(self, request, movie_id, resolution, segment):
        try:
            video = Video.objects.get(pk=movie_id)
        except Video.DoesNotExist:
            raise Http404("Video not found")
        
        if not segment.endswith('.ts'):
            raise Http404("Invalid segment format")
        
        filename, _ = os.path.splitext(os.path.basename(video.url.path))
        filename = filename.replace('_master', '') 
        filename = filename[0:20]
        
        segment_path = os.path.join(
            settings.MEDIA_ROOT,
            'uploads/videos/converted',
            f'{filename}_{resolution}',
            segment
        )
        
        if not os.path.exists(segment_path):
            raise Http404(f"Segment not found: {segment_path}")
        
        return FileResponse(
            open(segment_path, 'rb'),
            content_type='video/MP2T'
        )


class VideoProgressListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = VideoProgressSerializer

    def get_queryset(self):
        user = self.request.user
        profile = None
        if not user.is_authenticated:
            return VideoProgress.objects.none()
        profile = user.abstract_user

        if not user.is_authenticated:
            return VideoProgress.objects.none()
        if not profile:
            return VideoProgress.objects.none()
        
        queryset = VideoProgress.objects.filter(profiles=profile)
        video = self.request.query_params.get("videoId")
        if video:
            queryset = queryset.filter(video=video)
        return queryset

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        if hasattr(self, 'existing_instance'):
            serializer = self.get_serializer(self.existing_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return response

    def perform_create(self, serializer):
        user = self.request.user
        profiles = user.abstract_user
        video = serializer.validated_data.get('video')
        existing = VideoProgress.objects.filter(profiles=profiles, video=video).first()

        if existing:
            self.existing_instance = existing
            return
        
        serializer.save(profiles=profiles)


class VideoProgressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = VideoProgressSerializer

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        queryset = VideoProgress.objects.filter(pk=pk)
        return queryset
    
    def perform_update(self, serializer):
        return super().perform_update(serializer)
    
class CurrentVideoConvertProgressListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = CurrentVideoConvertProgressSerializer
    queryset = CurrentVideoConvertProgress.objects.all() 

class CurrentVideoConvertProgressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = CurrentVideoConvertProgressSerializer
    queryset = CurrentVideoConvertProgress.objects.all() 
    
class ServeMediaView(APIView):
    def get(self, request, path):
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        
        if not os.path.exists(file_path):
            raise Http404("File not found")
        
        if not os.path.abspath(file_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
            raise Http404("Invalid path")
        
        content_type = 'application/octet-stream'
        if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif file_path.endswith('.png'):
            content_type = 'image/png'
        elif file_path.endswith('.gif'):
            content_type = 'image/gif'
        
        return FileResponse(
            open(file_path, 'rb'),
            content_type=content_type
        )

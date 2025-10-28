from rest_framework import serializers
from service_app.models import Video
import os

'''
will validate and return a Video -> for VideosListView and create a new video
'''   
class VideosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'
    
    def validate(self, data):
        if 'url' in data and data['url']:
            self.validate_video_file(data['url'])
        return data

    def validate_video_file(self, file):
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        file_name = file.name.lower()
        file_extension = os.path.splitext(file_name)[1]
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError( f"Ungültiges Dateiformat. Erlaubte Formate: {', '.join(allowed_extensions)}" )
    
    def create(self, validated_data):
        video = super().create(validated_data)
        return video

    
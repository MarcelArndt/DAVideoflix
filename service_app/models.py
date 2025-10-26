from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()
    category = models.CharField(max_length=65, default="",)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail_url = models.FileField(upload_to="uploads/thumbnails", blank=True)
    url = models.FileField(upload_to="uploads/videos/originals")
    is_converted = models.BooleanField(default=False)
    current_convert_state = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f'Id: {self.pk} | HeadLine: {self.title} |  Genre:{self.category} | created at: {self.created_at}' 


class VideoProgress(models.Model):
    updated_at = models.DateTimeField(auto_now=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    current_time = models.FloatField()
    is_finished = models.BooleanField(default=False)


class CurrentVideoConvertProgress(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='video_convert_progress')

from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()
    category = models.CharField(max_length=65, default="",)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail_url = models.FileField(upload_to="uploads/thumbnails", blank=True)
    url = models.FileField(upload_to="uploads/videos/originals")

    def __str__(self):
        return f'Id: {self.pk} | HeadLine: {self.title} |  Genre:{self.category} | created at: {self.created_at}' 

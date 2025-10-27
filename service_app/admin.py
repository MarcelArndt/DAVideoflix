from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    readonly_fields = ('is_converted', 'current_convert_state')
    list_display = ('title', 'category', 'url')
    fields = ('title', 'description', 'category', 'url', 'thumbnail_url')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['url'].label = 'Video-URL'
        return form
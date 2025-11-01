from django.contrib import admin
from .models import Video

'''
   def get_form() -> will ste Url's label to Video-URL
'''
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    readonly_fields = ()
    list_display = ('title', 'category', 'url')
    fields = ('title', 'description', 'category', 'url', 'thumbnail_url')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['url'].label = 'Video-URL'
        return form
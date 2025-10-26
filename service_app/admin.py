from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    # Felder, die angezeigt werden, aber **nicht editierbar** sind
    readonly_fields = ('thumbnail_url', 'is_converted', 'current_convert_state')

    # Optional: Liste der Felder, die im Admin angezeigt werden sollen
    list_display = ('title', 'category', 'is_converted', 'current_convert_state',)

    # Optional: welche Felder im Formular sichtbar sind
    fields = ('title', 'description', 'category', 'url')
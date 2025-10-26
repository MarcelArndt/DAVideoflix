import os
import subprocess
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Video, VideoProgress, CurrentVideoConvertProgress
from django.conf import settings
import django_rq
import glob
import shutil
import re
import os
from dotenv import load_dotenv
load_dotenv()

ISDEBUG = True if os.environ.get("DEBUG", default="True") == "True" else False

RESOLUTIONS = {
        'videos': {
            '1080p': '1920x1080',
            '720p': '1280x720',
            '480p': '854x480',
            '360p': '640x360',
        },
        'thumbnails': '270:150'
    }


@receiver(post_save, sender=Video)
def generate_video_data(sender, instance, created, **kwargs):
    if not created or not instance.url:
        return
    if not ISDEBUG:
        queue = django_rq.get_queue('default', autocommit=True)
        queue.enqueue(generate_video_versions, instance)
    else: 
        generate_video_versions(instance)

def generate_video_versions(instance):
    base_output_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/videos/converted')
    os.makedirs(base_output_dir, exist_ok=True)
    
    try:
        video = instance.url.path
        generate_video_thumbnail(instance)
        filename, file_ending = os.path.splitext(os.path.basename(video))
        filename = filename[0:20]
        
        for resolution, size in RESOLUTIONS['videos'].items():
            resolution_dir = os.path.join(base_output_dir, f'{filename}_{resolution}')
            os.makedirs(resolution_dir, exist_ok=True)
            output_path = os.path.join(resolution_dir, 'index.m3u8')
            try:
                ffmpeg_converting_process(filename, size, resolution, video, resolution_dir, output_path)
            except subprocess.CalledProcessError as error:
                print(f"[ffmpeg] Fehler bei {resolution}: {error}")
        
        master_path = generate_master_playlist(filename, base_output_dir)
        save_new_video_path(instance, master_path)
        
    except Exception as error:
        print(f'something went Wrong! {error}')
    finally:
        CurrentVideoConvertProgress.objects.filter(video=instance).delete()


def ffmpeg_converting_process(filename, size, resolution, video, output_dir, output_path):
    """
    output_dir ist jetzt der Auflösungs-spezifische Ordner (z.B. demon_slayer_480p/)
    output_path ist jetzt der Pfad zur index.m3u8 in diesem Ordner
    """
    cmd = [
        'ffmpeg', '-i', video,
        '-vf', f'scale={size}',
        '-c:v', 'libx264', '-crf', '23', '-preset', 'medium',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
        '-g', '48', '-keyint_min', '48', '-sc_threshold', '0',
        '-force_key_frames', 'expr:gte(t,n_forced*2)',
        '-max_muxing_queue_size', '9999',
        '-f', 'hls',
        '-hls_time', '6',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', os.path.join(output_dir, 'segment%03d.ts'),
        output_path
    ]
    subprocess.run(cmd, check=True)
    

def save_new_video_path(instance, master_path):
    relative_path = os.path.relpath(master_path, settings.MEDIA_ROOT)
    instance.url.name = relative_path
    instance.save()


def generate_master_playlist(filename, output_dir):
    master_playlist_path = os.path.join(output_dir, f'{filename}_master.m3u8')
    bandwidth_map = {
        '1080p': 5000000,
        '720p': 3000000,
        '480p': 1500000,
        '360p': 800000,
    }
    with open(master_playlist_path, 'w') as file:
        file.write('#EXTM3U\n')  # Wichtig!
        for resolution, size in RESOLUTIONS['videos'].items():
            bandwidth = bandwidth_map.get(resolution, 1000000)
            file.write(f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={size}\n')
            file.write(f'{filename}_{resolution}/index.m3u8\n')
    return master_playlist_path


def get_video_duration(video_path):
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of',
            'default=noprint_wrappers=1:nokey=1', video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        duration = float(result.stdout.strip())
        if duration <= 0.0:
            duration = 1.0
        screenshot_time = duration / 3
        return screenshot_time  
    except:
        print('Fehler beim Abrufen der Videodatei.')
        return 1


def generate_video_thumbnail(instance):
    original_video_path = instance.url.path
    output_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/thumbnails')
    os.makedirs(output_dir, exist_ok=True)
    screenshot_time = get_video_duration(original_video_path)
    thumbnail_path = os.path.join(output_dir, f"{instance.id}_thumb.jpg")
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(screenshot_time),
        '-i', original_video_path,
        '-vframes', '1',
        '-vf', f"scale={RESOLUTIONS['thumbnails']}",
        thumbnail_path
    ]
    try:
        subprocess.run(cmd, check=True)
        instance.thumbnail_url.name = f"uploads/thumbnails/{instance.id}_thumb.jpg"
        instance.save()
    except subprocess.CalledProcessError as e:
        print(f"[ffmpeg] Fehler bei Thumbnail: {e}")



@receiver(post_delete, sender=Video)
def delete_file(sender, instance, *args, **kwargs):
    if not ISDEBUG:
        queue = django_rq.get_queue('default', autocommit=True)
        queue.enqueue(delete_video, instance)
    else: 
        delete_video(instance)


def delete_video(instance):
    delete_thumbnail(instance)
    delete_all_video(instance)
    delete_all_progress(instance)


def delete_all_progress(instance):
    videoId = instance.id
    queryset =  VideoProgress.objects.filter(video = videoId)
    deleted_count, _ = queryset.delete()


def delete_thumbnail(instance):
    if instance.thumbnail_url:
        thumb_path = os.path.join(settings.MEDIA_ROOT, instance.thumbnail_url.name)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
    

def delete_all_video(instance):
    if not instance.url:
        return
    original_path = instance.url.path
    filename, file_ending = os.path.splitext(os.path.basename(original_path))
    base_filename = re.sub(r'_(master|360p|480p|720p|1080p)$', '', filename)
    converted_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/videos/converted')

    deleteAllResolutionFile(converted_dir, base_filename)
    deleteAllMasterFile(converted_dir, base_filename)
    checkAndDeleteAnyFile(converted_dir, base_filename)
    deleteOriginalVideo(base_filename)
    CheckAndDeleteVideoUrl(original_path)

# 1. Lösche alle Auflösungs-Ordner (z.B. demon_slayer_480p/, demon_slayer_720p/)
def deleteAllResolutionFile(converted_dir, base_filename ):
    for resolution in ['360p', '480p', '720p', '1080p']:
        resolution_dir = os.path.join(converted_dir, f"{base_filename}_{resolution}")
        if os.path.exists(resolution_dir) and os.path.isdir(resolution_dir):
            shutil.rmtree(resolution_dir)  # Löscht Ordner mit allem Inhalt
            print(f"Gelöscht: {resolution_dir}")

 # 2. Lösche die Master-Playlist
def deleteAllMasterFile(converted_dir, base_filename ):
    master_playlist = os.path.join(converted_dir, f"{base_filename}_master.m3u8")
    if os.path.exists(master_playlist):
        os.remove(master_playlist)
        print(f"Gelöscht: {master_playlist}")


# 3. Fallback: Lösche alte einzelne Dateien (falls noch welche existieren)
def checkAndDeleteAnyFile(converted_dir, base_filename ):
    pattern = os.path.join(converted_dir, f"{base_filename}_*")
    matching_files = glob.glob(pattern)
    for file in matching_files:
        if os.path.isfile(file):
            os.remove(file)
            print(f"Gelöscht (alt): {file}")

# 4. Lösche Original-Video
def deleteOriginalVideo(base_filename):
    original_video_path = os.path.join(
        settings.MEDIA_ROOT, 
        'uploads/videos/originals', 
        base_filename + ".mp4"
    )
    if os.path.exists(original_video_path):
        os.remove(original_video_path)
        print(f"Gelöscht: {original_video_path}")

# 5. Lösche den Pfad aus instance.url (falls anders als Original)
def CheckAndDeleteVideoUrl(original_path):
    if os.path.exists(original_path):
        os.remove(original_path)
        print(f"Gelöscht: {original_path}")


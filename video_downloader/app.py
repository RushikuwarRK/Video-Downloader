from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import yt_dlp as youtube_dl
import instaloader
import threading

app = Flask(__name__)

DOWNLOAD_PATH = 'downloads'
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Global variable to store download progress
progress = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    global progress
    try:
        data = request.get_json()
        download_type = data.get('type')
        url = data.get('url')
        progress = 0

        if download_type == 'insta-reel':
            threading.Thread(target=download_instagram_reel, args=(url,)).start()
        elif download_type == 'insta-post':
            threading.Thread(target=download_instagram_post, args=(url,)).start()
        elif download_type == 'yt-audio':
            threading.Thread(target=download_youtube_audio, args=(url,)).start()
        elif download_type == 'yt-video':
            threading.Thread(target=download_youtube_video, args=(url,)).start()
        else:
            return jsonify({'success': False, 'error': 'Invalid download type'})

        return jsonify({'success': True, 'downloadUrl': f"/downloads/{os.path.basename(url)}"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': True, 'error': str(e)})

@app.route('/progress')
def get_progress():
    global progress
    return jsonify({'progress': progress})

def download_instagram_reel(url):
    global progress
    try:
        L = instaloader.Instaloader(download_videos=True, download_pictures=False, download_comments=False, compress_json=False, download_geotags=False)
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        progress = 10  # Initializing progress

        print(f"Starting download for reel with shortcode: {shortcode}")
        L.download_post(post, target=DOWNLOAD_PATH)
        
        progress = 70  # Midway progress (depends on actual progress; adjust as necessary)
        
        downloaded_files = os.listdir(DOWNLOAD_PATH)
        print(f"Files in download directory: {downloaded_files}")

        media_files = [f for f in downloaded_files if f.startswith(shortcode) and f.endswith('.mp4')]
        if media_files:
            downloaded_file = os.path.join(DOWNLOAD_PATH, media_files[0])
            print(f"Downloaded reel file: {downloaded_file}")
            progress = 100
            return downloaded_file
        
        print("No media files found")
        progress = 100
        return None
    except Exception as e:
        progress = 100  # In case of failure
        raise Exception(f"Error downloading Instagram reel: {e}")


def download_instagram_post(url):
    global progress
    try:
        L = instaloader.Instaloader(download_videos=True, download_pictures=True, download_comments=False, compress_json=False, download_geotags=False)
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        progress = 10  # Initializing progress

        print(f"Starting download for post with shortcode: {shortcode}")
        L.download_post(post, target=DOWNLOAD_PATH)
        
        progress = 70  # Midway progress (adjust based on actual progress)

        downloaded_files = os.listdir(DOWNLOAD_PATH)
        print(f"Files in download directory: {downloaded_files}")

        media_files = [f for f in downloaded_files if f.startswith(shortcode) and (f.endswith('.jpg') or f.endswith('.mp4'))]
        if media_files:
            downloaded_file = os.path.join(DOWNLOAD_PATH, media_files[0])
            print(f"Downloaded post file: {downloaded_file}")
            progress = 100
            return downloaded_file

        print("No media files found")
        progress = 100
        return None
    except Exception as e:
        progress = 100  # In case of failure
        raise Exception(f"Error downloading Instagram post: {e}")


def download_youtube_audio(url):
    global progress
    try:
        ffmpeg_path = 'ffmpeg-2024-07-10-git-1a86a7a48d-full_build\\bin\\ffmpeg.exe'
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
            'ffmpeg_location': ffmpeg_path,
            'progress_hooks': [lambda d: update_progress(d)],  # Progress hook
        }

        progress = 10  # Initializing progress

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            audio_file = filename.rsplit('.', 1)[0] + '.mp3'
        
        progress = 100  # Completed
        return audio_file
    except Exception as e:
        progress = 100  # In case of failure
        raise Exception(f"Error downloading YouTube audio: {e}")

def update_progress(d):
    global progress
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 1)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        progress = int((downloaded_bytes / total_bytes) * 100)
        
        # Ensure progress does not exceed 100%
        if progress > 100:
            progress = 100


def download_youtube_video(url):
    global progress
    try:
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: update_progress(d)],  # Progress hook
        }

        progress = 10  # Initializing progress

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            print(f"Downloaded video file: {filename}")
        
        progress = 100  # Completed
        return filename
    except Exception as e:
        progress = 100  # In case of failure
        raise Exception(f"Error downloading YouTube video: {e}")

# Ensure that the same `update_progress` function is used

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_PATH, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1228)

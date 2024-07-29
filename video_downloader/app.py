from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import yt_dlp as youtube_dl
import instaloader

app = Flask(__name__)

DOWNLOAD_PATH = 'downloads'
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        download_type = data.get('type')
        url = data.get('url')

        if download_type == 'insta-reel':
            download_url = download_instagram_reel(url)
        elif download_type == 'insta-post':
            download_url = download_instagram_post(url)
        elif download_type == 'yt-audio':
            download_url = download_youtube_audio(url)
        elif download_type == 'yt-video':
            download_url = download_youtube_video(url)
        else:
            return jsonify({'success': False, 'error': 'Invalid download type'})

        if download_url:
            return jsonify({'success': True, 'downloadUrl': f"/downloads/{os.path.basename(download_url)}"})
        else:
            return jsonify({'success': False, 'error': 'Download but not name'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': True, 'error': str(e)})

def download_instagram_reel(url):
    try:
        L = instaloader.Instaloader(download_videos=True, download_pictures=False, download_comments=False, compress_json=False, download_geotags=False)
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        print(f"Starting download for reel with shortcode: {shortcode}")
        L.download_post(post, target=DOWNLOAD_PATH)
        
        # List the contents of the DOWNLOAD_PATH directory for debugging
        downloaded_files = os.listdir(DOWNLOAD_PATH)
        print(f"Files in download directory: {downloaded_files}")

        media_files = [f for f in downloaded_files if f.startswith(shortcode) and f.endswith('.mp4')]
        if media_files:
            downloaded_file = os.path.join(DOWNLOAD_PATH, media_files[0])
            print(f"Downloaded reel file: {downloaded_file}")
            return downloaded_file  # Return the first media file for simplicity
        print("No media files found")
        return None
    except Exception as e:
        raise Exception(f"Error downloading Instagram reel: {e}")

def download_instagram_post(url):
    try:
        L = instaloader.Instaloader(download_videos=True, download_pictures=True, download_comments=False, compress_json=False, download_geotags=False)
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        print(f"Starting download for post with shortcode: {shortcode}")
        L.download_post(post, target=DOWNLOAD_PATH)
        
        # List the contents of the DOWNLOAD_PATH directory for debugging
        downloaded_files = os.listdir(DOWNLOAD_PATH)
        print(f"Files in download directory: {downloaded_files}")

        media_files = [f for f in downloaded_files if f.startswith(shortcode) and (f.endswith('.jpg') or f.endswith('.mp4'))]
        if media_files:
            downloaded_file = os.path.join(DOWNLOAD_PATH, media_files[0])
            print(f"Downloaded post file: {downloaded_file}")
            return downloaded_file  # Return the first media file for simplicity
        print("No media files found")
        return None
    except Exception as e:
        raise Exception(f"Error downloading Instagram post: {e}")

def download_youtube_audio(url):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            audio_file = filename.rsplit('.', 1)[0] + '.mp3'
            print(f"Downloaded audio file: {audio_file}")
        
        return audio_file
    except Exception as e:
        raise Exception(f"Error downloading YouTube audio: {e}")

def download_youtube_video(url):
    try:
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            print(f"Downloaded video file: {filename}")
        
        return filename
    except Exception as e:
        raise Exception(f"Error downloading YouTube video: {e}")

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_PATH, filename)

if __name__ == '__main__':
    app.run(debug=True)

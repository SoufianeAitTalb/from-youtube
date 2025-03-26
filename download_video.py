import os
import yt_dlp


def download_video(video_id, download_folder="downloaded_videos"):
    try:
        os.makedirs(download_folder, exist_ok=True)
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            # More reliable format selection
            'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
            'outtmpl': f'{download_folder}/{video_id}.%(ext)s',
            'progress_hooks': [progress_callback],
            'phantomjs_path': "C:\\Program Files\\phantomjs-2.1.1-windows\\bin\\phantomjs.exe",

            # Additional fixes
            'merge_output_format': 'mp4',  # Force MP4 output
            'ignoreerrors': True,  # Continue on download errors
            'retries': 10,  # Increase retry attempts
            'fragment_retries': 10,
            'hls_use_mpegts': True,  # Better HLS handling
            'verbose': True  # Show more debug info
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading video: {video_id}")
            info = ydl.extract_info(youtube_url, download=True)

            if not info:
                raise ValueError("Failed to extract video info")

            # Get actual downloaded file path
            downloaded_file = ydl.prepare_filename(info)
            final_path = os.path.join(download_folder, os.path.basename(downloaded_file))

            if not os.path.exists(final_path):
                raise FileNotFoundError("Downloaded file not created")

            print(f"Download complete: {final_path}")
            return final_path

    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None


def progress_callback(d):
    if d['status'] == 'downloading':
        # Handle cases where total_bytes might be missing
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        if total and total > 0:
            percent = d['downloaded_bytes'] / total * 100
            print(f"Progress: {percent:.1f}%")
        else:
            # Show alternative progress info
            print(f"Downloaded {d.get('downloaded_bytes', 0):,} bytes")
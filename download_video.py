import os
import yt_dlp

def download_video(video_id, download_folder="downloaded_videos"):
    try:
        # Ensure the download folder exists
        os.makedirs(download_folder, exist_ok=True)

        # YouTube URL
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        # yt-dlp options
        ydl_opts = {
            'format': 'bestvideo[height<=2160]+bestaudio/best',  # Download best quality up to 1080p (or best available)
            'outtmpl': f'{download_folder}/{video_id}.%(ext)s',  # Output file name template
            'progress_hooks': [progress_callback],  # Add progress callback to show download progress
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading video: {video_id}")
            ydl.download([youtube_url])

            # Get the downloaded file's extension and name
            downloaded_file = f"{download_folder}/{video_id}.webm"  # After merging, it will be .webm
            print(f"Download complete for video: {video_id}")

            # Return the path of the downloaded file
            return downloaded_file

    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

# Progress callback function to show download progress
def progress_callback(d):
    if d['status'] == 'downloading':
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        print(f"Download Progress: {percent:.2f}%")

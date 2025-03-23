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
            # 'format': 'bestvideo[height<=1080]+bestaudio/best',  # Download best quality up to 1080p (or best available)
            'format': 'bestvideo[height<=480]+bestaudio[abr>=128][abr<=192]/best',
            #low audio quality
            # 'format': 'bestvideo[height<=144]+bestaudio[abr>=64][abr<=96]/best',
            'outtmpl': f'{download_folder}/{video_id}.%(ext)s',  # Output file name template
            'progress_hooks': [progress_callback],  # Add progress callback to show download progress
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading video: {video_id}")
            ydl.download([youtube_url])

            # Get the list of files in the download folder
            files = os.listdir(download_folder)

            # Find the downloaded file with the correct extension
            downloaded_file = None
            for file in files:
                if file.startswith(video_id):  # Check if the file matches the video ID
                    downloaded_file = os.path.join(download_folder, file)
                    break

            # Check if we found the downloaded file
            if downloaded_file:
                print(f"Download complete for video: {video_id}")
                return downloaded_file
            else:
                print("Error: Downloaded file not found.")
                return None
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

# Progress callback function to show download progress
def progress_callback(d):
    if d['status'] == 'downloading':
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        print(f"Download Progress: {percent:.2f}%")

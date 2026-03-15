
import requests
from yt_dlp import YoutubeDL
import time

def reproduce():
    video_id = "M6LboyWogFk" # Auto parts video from log
    print(f"Extracting info for {video_id}...")
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        
    subs = info.get('subtitles') or {}
    auto_subs = info.get('automatic_captions') or {}
    
    target_lang = 'en'
    url = None
    
    # Logic from main.py
    if target_lang in subs:
        for fmt in subs[target_lang]:
            if fmt.get('ext') == 'json3':
                url = fmt['url']
                break
    
    if not url and target_lang in auto_subs:
        for fmt in auto_subs[target_lang]:
            if fmt.get('ext') == 'json3':
                url = fmt['url']
                break
                
    if not url:
        print("No URL found")
        return

    print(f"Found URL: {url[:50]}...")
    
    # 1. Try without headers (Original)
    print("\n--- Attempt 1: No Headers ---")
    try:
        resp = requests.get(url)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Response: {resp.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Try with Headers
    print("\n--- Attempt 2: With User-Agent ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Success with headers!")
        else:
            print(f"Response: {resp.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reproduce()

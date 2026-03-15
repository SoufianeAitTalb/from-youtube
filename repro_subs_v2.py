
import requests
from yt_dlp import YoutubeDL
import time
import random

def reproduce():
    video_id = "M6LboyWogFk"
    
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
    
    # Logic from FIX
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    if info.get('http_headers') and info['http_headers'].get('User-Agent'):
        print(f"Using yt-dlp UA: {info['http_headers']['User-Agent']}")
        headers['User-Agent'] = info['http_headers']['User-Agent']
    else:
        print("Using hardcoded Chrome UA")

    for attempt in range(3):
        try:
            print(f"Fetching (Attempt {attempt+1})...")
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                print("Success!")
                print(f"Data length: {len(resp.text)}")
                break
            elif resp.status_code == 429:
                wait = (2 ** attempt)
                print(f"Got 429, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"Failed: {resp.status_code}")
                print(resp.text[:200])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    reproduce()

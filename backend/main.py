from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.api import router as api_router
import requests
import json
import re
import time
import random
import numpy as np
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

app = FastAPI(title="YouTube Video Processing API")

# Mount static files
app.mount("/outputs", StaticFiles(directory="processing_output"), name="outputs")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to YouTube Processing API"}

# Helper: Fetch and Parse Subtitles
def get_params_for_subtitles(info, video_id=None):
    subs = info.get('subtitles') or {}
    auto_subs = info.get('automatic_captions') or {}
    
    # Priority: Manual 'en' -> Auto 'en' -> Manual 'auto' -> ...
    # Prefer json3 format for easy parsing
    target_lang = 'en'
    
    url = None
    
    # Try finding in manual
    if target_lang in subs:
        for fmt in subs[target_lang]:
            if fmt.get('ext') == 'json3':
                url = fmt['url']
                break
    
    # Try finding in auto
    if not url and target_lang in auto_subs:
        for fmt in auto_subs[target_lang]:
            if fmt.get('ext') == 'json3':
                url = fmt['url']
                break
                
    if not url: return []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Use headers from yt-dlp info if available
    if info.get('http_headers') and info['http_headers'].get('User-Agent'):
        headers['User-Agent'] = info['http_headers']['User-Agent']

    resp = None
    for attempt in range(3):
        try:
            print(f"Fetching subtitles from: {url} (Attempt {attempt+1})")
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                break
            elif resp.status_code == 429:
                wait_time = (2 ** attempt) + random.random()
                print(f"Got 429, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                print(f"Subtitle fetch failed: {resp.status_code} - {resp.text[:200]}")
                # For non-429 errors, we might want to fail fast or continue. 
                # YouTube often returns 4xx for expired URLs, so maybe just failing is correct.
                # But let's retry 403 just in case? Usually 403 is fatal without fresh sig.
                pass 
        except Exception as e:
            print(f"Request error: {e}")
            time.sleep(1)
            
    if not resp or resp.status_code != 200:
        print("Failed to fetch subtitles after retries.")
        return []

    try:
        data = resp.json()
        
        # Parse JSON3 to simple list of {start, end, text}
        events = []
        if 'events' in data:
            for ev in data['events']:
                if 'tStartMs' not in ev: continue
                start = ev['tStartMs'] / 1000.0
                duration = ev.get('dDurationMs', 0) / 1000.0
                end = start + duration
                
                # Extract text
                text = ""
                if 'segs' in ev:
                    text = "".join([s.get('utf8', '') for s in ev['segs']])
                
                events.append({
                    "start": start,
                    "end": end,
                    "text": text.strip()
                })
        return events
    except Exception as e:
        print(f"Error fetching subtitles: {e}")
        try:
             print(f"Response content debug: {resp.text[:500]}")
        except: pass
        
    # Fallback to youtube-transcript-api if available and requests failed
    if YouTubeTranscriptApi and video_id:
        print("Trying youtube-transcript-api fallback...")
        try:
            # Handle version differences (static vs instance)
            if hasattr(YouTubeTranscriptApi, 'get_transcript'):
                data = YouTubeTranscriptApi.get_transcript(video_id)
                # Standad format: list of dicts {text, start, duration}
                events = []
                for item in data:
                    events.append({
                        "start": item['start'],
                        "end": item['start'] + item['duration'],
                        "text": item['text']
                    })
                print(f"Fallback success! Found {len(events)} lines.")
                return events
            else:
                # Assuming quirk 1.2.3 version (instance method)
                api = YouTubeTranscriptApi()
                trans = api.fetch(video_id)
                if trans and hasattr(trans, 'snippets'):
                    events = []
                    for s in trans.snippets:
                         events.append({
                            "start": s.start,
                            "end": s.start + s.duration,
                            "text": s.text
                        })
                    print(f"Fallback success! Found {len(events)} lines.")
                    return events
        except Exception as e:
            print(f"Fallback failed: {e}")

    return []

def align_to_sentence(start, end, subtitles):
    if not subtitles:
        return start, end
        
    # Find active subtitles in this range
    relevant_indices = [i for i, s in enumerate(subtitles) if s['end'] > start and s['start'] < end]
    
    if not relevant_indices:
        return start, end
        
    first_idx = relevant_indices[0]
    last_idx = relevant_indices[-1]
    
    # Expand Left: Try to include the start of the first sentence
    # Heuristic: If the first relevant subtitle starts with a lowercase, it might be mid-sentence.
    # Look back for a period or capital letter.
    # Simple heuristic: Just snap to the start of the first subtitle block found
    # But checking if we missed the start of a sentence:
    
    # Look backwards from first_idx to find a sentence break
    # Max lookback 5 seconds
    curr_start = subtitles[first_idx]['start']
    
    # Ideally we find punctuation in previous subs
    # For now, let's just snap to the start of the first intercepted subtitle block
    new_start = subtitles[first_idx]['start']
    
    # Expand Right: Find end of sentence
    new_end = subtitles[last_idx]['end']
    
    # Try to find a period/punctuation in subsequent blocks
    curr_idx = last_idx
    # Look forward up to 10 seconds or 3 blocks to find a sentence end
    lookahead_count = 0
    while curr_idx < len(subtitles) - 1 and lookahead_count < 5:
        sub = subtitles[curr_idx]
        text = sub['text']
        if text and text[-1] in ['.', '?', '!']:
            new_end = sub['end']
            break # Found sentence end
        
        # Check next
        curr_idx += 1
        lookahead_count += 1
        new_end = subtitles[curr_idx]['end'] # Extend to include next block tentatively
        
        if (new_end - new_start) > 60: # Don't exceed Shorts limit
            new_end = sub['end'] # Revert to previous safe end
            break
            
    # Constraints check
    duration = new_end - new_start
    if duration > 60:
        # If alignment pushed us over 60s, revert to raw or trim
        # Priority: Keep start, trim end
        new_end = new_start + 60
    
    if duration < 5:
        # If alignment resulted in too short (e.g. single word), revert to original range
        return start, end

    return round(new_start, 2), round(new_end, 2)

import google.generativeai as genai
import os
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

# Configure Gemini
# NOTE: In production, use os.environ.get("GEMINI_API_KEY")
GENAI_API_KEY = "AIzaSyBa5XEk8enhhzI-QCJptFOigttDyYwmMFU"
genai.configure(api_key=GENAI_API_KEY)

# Helper: Analyze with Gemini
def analyze_with_gemini(transcript_events):
    if not transcript_events:
        return None

    full_text = " ".join([e['text'] for e in transcript_events])
    
    # Estimate token count roughly (4 chars per token) to avoid limit? 
    # Gemini 1.5 Flash has huge context, so 5 mins of text is fine.

    prompt = f"""
    You are an expert video editor specialized in creating viral YouTube Shorts and TikToks.
    Below is a transcript from a high-engagement section of a video.
    
    Your goal: Identify the SINGLE most engaging, funny, or interesting continuous segment suitable for a Short (15 to 60 seconds).
    
    Transcript:
    "{full_text}"
    
    Instructions:
    1. Select a continuous part that stands on its own (has a hook and a punchline/conclusion).
    2. Ensure the duration is between 15s and 60s (approx 40-160 words).
    3. Return the EXACT start phrase (first 5-10 words) and end phrase (last 5-10 words) of your selected clip.
    
    Output Format (JSON):
    {{
        "start_phrase": "...",
        "end_phrase": "...",
        "reason": "..."
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"Gemini Analysis Failed: {e}")
        return None

def find_timestamps_from_text(start_phrase, end_phrase, events):
    # Fuzzy match logic or simple strict match
    # Since Gemini returns exact text from transcript, we try to find the best matching events.
    
    # Simplify text for matching (lowercase, remove punctuation)
    def clean(t): return re.sub(r'[^\w\s]', '', t.lower())
    
    start_phrase_clean = clean(start_phrase)
    end_phrase_clean = clean(end_phrase)
    
    start_time = None
    end_time = None
    
    # 1. Find Start
    for i, ev in enumerate(events):
        ev_text = clean(ev['text'])
        # Check if start phrase is in this event or starts here
        if start_phrase_clean in ev_text or ev_text.startswith(start_phrase_clean[:10]):
            start_time = ev['start']
            # Refine: If we matched inside the segment, maybe interpolate? 
            # For now, safe start is the event start.
            break
            
    # 2. Find End (search from start index?)
    for ev in events:
        if start_time and ev['start'] < start_time: continue
        
        ev_text = clean(ev['text'])
        if end_phrase_clean in ev_text or ev_text.endswith(end_phrase_clean[-10:]):
            end_time = ev['end']
    
    if start_time is not None and end_time is not None:
        return start_time, end_time
    
    return None, None

@app.get("/most-replayed")
def get_replayed_parts(videoId: str, numberOfParts: int = None):
    print(f"Analyzing viral segments for {videoId} (Target: {'Auto' if numberOfParts is None else numberOfParts} parts)")
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'nocheckcertificate': True, 
        'socket_timeout': 15, 
        'no_warnings': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Fetch metadata
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={videoId}", download=False)
            
            # Fetch subtitles
            subtitles = get_params_for_subtitles(info, videoId)
            if subtitles:
                print(f"Fetched {len(subtitles)} subtitle lines.")

            if 'heatmap' not in info:
                print("No heatmap data found.")
                return {"replayedParts": []}

            heatmap = info['heatmap'] 
            times = np.array([(p['start_time'] + p['end_time'])/2 for p in heatmap])
            values = np.array([p.get('value', 0) for p in heatmap])
            
            if len(values) < 5: return {"replayedParts": []}

            # Smoothing
            window_size = 5
            kernel = np.ones(window_size) / window_size
            smoothed_values = np.convolve(values, kernel, mode='same')
            
            # Peak Detection
            peaks = []
            global_threshold = np.mean(smoothed_values) + 0.5 * np.std(smoothed_values)
            for i in range(1, len(smoothed_values) - 1):
                if (smoothed_values[i] > smoothed_values[i-1] and 
                    smoothed_values[i] > smoothed_values[i+1] and 
                    smoothed_values[i] > global_threshold):
                    peaks.append(i)
            
            peaks.sort(key=lambda i: smoothed_values[i], reverse=True)
            
            # Auto-detect limit
            if numberOfParts is None:
                if not peaks: max_limit = 0
                else:
                    max_peak_val = smoothed_values[peaks[0]]
                    max_limit = 0
                    for p_idx in peaks:
                        if max_peak_val > 0 and smoothed_values[p_idx] >= (max_peak_val * 0.6): 
                            max_limit += 1
                        else: break
                    max_limit = max(1, min(max_limit, 10))
            else:
                max_limit = numberOfParts

            selected_parts = []
            
            def is_overlapping(start, end, parts):
                for p in parts:
                    if max(start, p['start']) < min(end, p['end']): 
                        return True
                return False

            for peak_idx in peaks:
                if len(selected_parts) >= max_limit: break
                
                # --- BROAD REGION GROWING (Search Window) ---
                # Expand up to ~5 mins total (2.5m each side) to give Gemini context
                left_idx = peak_idx
                right_idx = peak_idx
                current_value = smoothed_values[peak_idx]
                retention_floor = current_value * 0.3 # Lower floor for broad context
                
                # 150s * 2 approx 5 mins max
                MAX_SEARCH_SEC = 150 
                
                while left_idx > 0:
                     if smoothed_values[left_idx-1] < retention_floor: break
                     left_idx -= 1
                     if (times[peak_idx] - times[left_idx]) > MAX_SEARCH_SEC: break

                while right_idx < len(smoothed_values) - 1:
                    if smoothed_values[right_idx+1] < retention_floor: break
                    right_idx += 1
                    if (times[right_idx] - times[peak_idx]) > MAX_SEARCH_SEC: break
                
                search_start = heatmap[left_idx]['start_time']
                search_end = heatmap[right_idx]['end_time']
                
                # Default "dumb" cut (Fallback)
                final_start = search_start
                final_end = search_end
                
                # Constrain fallback to 60s around peak
                peak_time = times[peak_idx]
                fallback_start = max(0, peak_time - 30)
                fallback_end = peak_time + 30
                
                gemini_success = False

                # --- GEMINI ANALYSIS ---
                if subtitles:
                    # extract transcript for search window
                    window_subs = [s for s in subtitles if s['end'] > search_start and s['start'] < search_end]
                    
                    if len(window_subs) > 5: # Only analyze if we have enough context
                        print(f"Asking Gemini to analyze {len(window_subs)} lines region ({search_start:.1f}-{search_end:.1f})...")
                        analysis = analyze_with_gemini(window_subs)
                        
                        if analysis:
                            print(f"Gemini proposed: {analysis.get('reason')}")
                            g_start, g_end = find_timestamps_from_text(analysis['start_phrase'], analysis['end_phrase'], window_subs)
                            
                            if g_start is not None and g_end is not None:
                                duration = g_end - g_start
                                if 10 <= duration <= 90: # Allow slight flexibility for formatting
                                    final_start = g_start
                                    final_end = g_end
                                    gemini_success = True
                
                if not gemini_success:
                    print(f"  > Fallback to heatmap alignment (Gemini success: {gemini_success})")
                    # Fallback method: simple sentence alignment on 60s chunk
                    final_start = fallback_start
                    final_end = fallback_end
                    if subtitles:
                        final_start, final_end = align_to_sentence(final_start, final_end, subtitles)

                # Final constraints check
                duration = final_end - final_start
                if duration > 65: # Hard cap
                    center = (final_start + final_end) / 2
                    final_start = center - 30
                    final_end = center + 30
                
                print(f"  > Finalizing Clip: {final_start}-{final_end} (Method: {'gemini' if gemini_success else 'heatmap'})")

                if not is_overlapping(final_start, final_end, selected_parts):
                     selected_parts.append({
                        "start": round(final_start, 1),
                        "end": round(final_end, 1),
                        "position": len(selected_parts) + 1,
                        "duration": round(final_end - final_start, 1),
                        "score": round(float(smoothed_values[peak_idx]), 2),
                        "method": "gemini" if gemini_success else "heatmap_alignment"
                    })
            
            selected_parts.sort(key=lambda x: x['start'])
            for i, part in enumerate(selected_parts):
                part['position'] = i + 1
            
            print(f"Analyze complete. Found {len(selected_parts)} parts.")
            return {"replayedParts": selected_parts}

    except Exception as e:
        print(f"Error extracting heatmap: {e}")
        return {"replayedParts": [], "error": str(e)}

    except DownloadError as e:
        print(f"yt-dlp DownloadError: {e}")
        return {"replayedParts": []}
    except Exception as e:
        print(f"Error fetching replayed parts: {e}")
        return {"replayedParts": []}

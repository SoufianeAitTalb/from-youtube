from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.api import router as api_router
import requests
import json
import re
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
def get_params_for_subtitles(info):
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

    try:
        resp = requests.get(url)
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
            
            # Fetch subtitles for alignment
            subtitles = get_params_for_subtitles(info)
            if subtitles:
                print(f"Fetched {len(subtitles)} subtitle lines for alignment.")

            if 'heatmap' not in info:
                print("No heatmap data found.")
                return {"replayedParts": []}

            heatmap = info['heatmap'] # List of {start_time, end_time, value}
            
            # 1. Data Preparation
            # Convert to numpy arrays for signal processing
            times = np.array([(p['start_time'] + p['end_time'])/2 for p in heatmap])
            values = np.array([p.get('value', 0) for p in heatmap])
            
            if len(values) < 5:
                # Fallback for very short/no data
                return {"replayedParts": []}

            # 2. Smoothing (Simple Moving Average)
            window_size = 5
            kernel = np.ones(window_size) / window_size
            smoothed_values = np.convolve(values, kernel, mode='same')
            
            # 3. Peak Detection
            # Find local maxima indices
            peaks = []
            # Calculate dynamic global threshold (mean + 0.5std) to ignore low-interest noise
            global_threshold = np.mean(smoothed_values) + 0.5 * np.std(smoothed_values)
            
            for i in range(1, len(smoothed_values) - 1):
                if (smoothed_values[i] > smoothed_values[i-1] and 
                    smoothed_values[i] > smoothed_values[i+1] and 
                    smoothed_values[i] > global_threshold):
                    peaks.append(i)
            
            # Sort peaks by intensity (highest value first)
            peaks.sort(key=lambda i: smoothed_values[i], reverse=True)
            
            # Auto-detect limit: Top peaks usually cover the best viral moments for Shorts
            # Only take peaks that are at least 60% as strong as the max peak
            if numberOfParts is None:
                if not peaks:
                     max_limit = 0
                else:
                    max_peak_val = smoothed_values[peaks[0]]
                    max_limit = 0
                    for p_idx in peaks:
                        # Safety check for divide by zero (though peak > threshold > 0)
                        if max_peak_val > 0 and smoothed_values[p_idx] >= (max_peak_val * 0.6): 
                            max_limit += 1
                        else:
                            break
                    # Allow up to 10 parts if they are high quality
                    max_limit = max(1, min(max_limit, 10))
            else:
                max_limit = numberOfParts

            selected_parts = []
            
            def is_overlapping(start, end, parts):
                for p in parts:
                    if max(start, p['start']) < min(end, p['end']): 
                        return True
                return False

            # 4. Region Growing & Selection
            for peak_idx in peaks:
                if len(selected_parts) >= max_limit:
                    break
                
                # Expand to find context
                left_idx = peak_idx
                right_idx = peak_idx
                current_value = smoothed_values[peak_idx]
                
                # Dynamic Thresholds based on this specific peak's height
                retention_floor = current_value * 0.5 
                
                # Expand Left (Look for the "Hook" - steep rise)
                while left_idx > 0:
                     if smoothed_values[left_idx-1] < retention_floor: break
                     left_idx -= 1
                     if (times[peak_idx] - times[left_idx]) > 45: break

                # Expand Right (Resolution)
                while right_idx < len(smoothed_values) - 1:
                    if smoothed_values[right_idx+1] < retention_floor: break
                    right_idx += 1
                    if (times[right_idx] - times[peak_idx]) > 45: break
                
                # 5. Optimization for Shorts format
                start_time = heatmap[left_idx]['start_time']
                end_time = heatmap[right_idx]['end_time']
                duration = end_time - start_time
                
                # Enforce Constraints (15s - 60s)
                TARGET_MIN = 15
                TARGET_MAX = 60
                
                if duration < TARGET_MIN:
                    # Expand symmetrically to meet min duration
                    padding = (TARGET_MIN - duration) / 2
                    start_time = max(0, start_time - padding)
                    end_time = end_time + padding
                elif duration > TARGET_MAX:
                    # Trim. Center the peak.
                    center = times[peak_idx]
                    start_time = max(0, center - (TARGET_MAX * 0.4)) # 40% before peak
                    end_time = start_time + TARGET_MAX
                
                # --- SUBTITLE ALIGNMENT START ---
                if subtitles:
                    aligned_start, aligned_end = align_to_sentence(start_time, end_time, subtitles)
                    # Only apply if it makes sense (not drifting too far from heatmap peak)
                    # Check if peak is still inside or close
                    peak_time = times[peak_idx]
                    if aligned_start <= peak_time and aligned_end >= peak_time:
                         start_time = aligned_start
                         end_time = aligned_end
                # --- SUBTITLE ALIGNMENT END ---

                if not is_overlapping(start_time, end_time, selected_parts):
                     selected_parts.append({
                        "start": round(start_time, 1),
                        "end": round(end_time, 1),
                        "position": len(selected_parts) + 1,
                        "duration": round(end_time - start_time, 1),
                        "score": round(float(smoothed_values[peak_idx]), 2)
                    })
            
            # Sort by chronological order for final output
            selected_parts.sort(key=lambda x: x['start'])
            for i, part in enumerate(selected_parts):
                part['position'] = i + 1

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

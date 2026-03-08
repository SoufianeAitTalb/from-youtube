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
    if not video_id:
        return []

    print("Fetching subtitles using youtube-transcript-api...")
    
    if not YouTubeTranscriptApi:
        print("youtube-transcript-api not installed/available.")
        return []

    try:
        # 1. Try list_transcripts (Modern API)
        if hasattr(YouTubeTranscriptApi, 'list_transcripts'):
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Priority: Manual English -> Manual Native -> Generated English -> Generated Native -> Any
                transcript = None
                
                try:
                    transcript = transcript_list.find_manually_created_transcript(['en'])
                except:
                    try:
                        transcript = transcript_list.find_generated_transcript(['en'])
                    except:
                        # Iterate and pick first available (any language)
                        for t in transcript_list:
                            print(f"Found transcript: {t.language} ({t.language_code})")
                            transcript = t
                            break
                
                if transcript:
                    print(f"Fetching transcript content for: {transcript.language}...")
                    data = transcript.fetch()
                    print("Transcript fetch complete.")
                    
                    events = []
                    for item in data:
                        events.append({
                            "start": item['start'],
                            "end": item['start'] + item['duration'],
                            "text": item['text']
                        })
                    print(f"Success! Found {len(events)} lines.")
                    return events
                else:
                    print("No suitable transcript found in list.")
                    
            except Exception as e:
                 print(f"Error listing transcripts: {e}")
                 # Fall through to legacy/backup methods
        
        # 2. Try get_transcript (Static Fallback)
        if hasattr(YouTubeTranscriptApi, 'get_transcript'):
            print("Using get_transcript fallback...")
            try:
                data = YouTubeTranscriptApi.get_transcript(video_id) # Defaults to 'en'
            except Exception as e:
                 print(f"get_transcript('en') failed: {e}")
                 # Try common languages
                 print("Trying common languages: ar, fr, es, de...")
                 data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'ar', 'fr', 'es', 'de'])

            events = []
            for item in data:
                events.append({
                    "start": item['start'],
                    "end": item['start'] + item['duration'],
                    "text": item['text']
                })
            print(f"Success! Found {len(events)} lines.")
            return events

        # 3. Legacy / Instance Fallback (for older versions/forks)
        else:
            print("Using legacy instance fallback...")
            api = YouTubeTranscriptApi()
            try:
                print("Attempting to fetch with language list...")
                trans = api.fetch(video_id, languages=['en', 'ar', 'fr', 'es', 'de'])
            except TypeError:
                print("Legacy fetch does not support 'languages', trying default...")
                trans = api.fetch(video_id)
            except Exception as e:
                print(f"Legacy fetch failed with languages: {e}")
                trans = api.fetch(video_id) # Last ditch

            if trans:
                 # Handle different return types
                if isinstance(trans, list):
                     events = []
                     for item in trans:
                        events.append({
                            "start": item['start'],
                            "end": item['start'] + item['duration'],
                            "text": item['text']
                        })
                     print(f"Success! Found {len(events)} lines.")
                     return events
                elif hasattr(trans, 'snippets'):
                    events = []
                    for s in trans.snippets:
                         events.append({
                            "start": s.start,
                            "end": s.start + s.duration,
                            "text": s.text
                        })
                    print(f"Success! Found {len(events)} lines.")
                    return events
                else:
                     print(f"Unknown transcript object type: {type(trans)}")

    except Exception as e:
        print(f"All subtitle fetch methods failed: {e}")

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
GENAI_API_KEY = "AIzaSyC5cstglRSP2q_J5XxE7Any4TzdKa6IvZQ"
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
    2. **STRICT CONSTRAINT: The duration MUST be between 30 and 55 seconds.**
       - 60 seconds is the ABSOLUTE HARD LIMIT. Do not even risk 59s. Target 45s.
       - If the interesting section is longer, find the *best continuous 45s segment* within it.
    3. Return the EXACT start phrase (first 5-10 words) and end phrase (last 5-10 words) of your selected clip. 
       IMPORTANT: The start_phrase and end_phrase MUST be exact substrings from the provided transcript. DO NOT TRANSLATE them. Use the same language as the transcript.
    
    Output Format (JSON):
    {{
        "start_phrase": "...",
        "end_phrase": "...",
        "reason": "..."
    }}
    """
    
    patience = 20
    
    models_to_try = [
        'models/gemini-3-flash-preview', 
        'models/gemini-flash-latest'
    ]
    
    for i, model_name in enumerate(models_to_try):
        is_last_model = (i == len(models_to_try) - 1)
        # If it's the last resort (Flash), retry aggressively with waiting.
        # If it's the first preference (Pro), fail fast to switch to Flash.
        retries = 3 if is_last_model else 1
        
        for attempt in range(retries):
            try:
                print(f"Requesting Gemini analysis using: {model_name} (Attempt {attempt+1})...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                result = json.loads(response.text)
                return result
            except Exception as e:
                is_rate_limit = "429" in str(e) or "Quota exceeded" in str(e)
                
                if is_rate_limit:
                    if is_last_model and attempt < retries - 1:
                        wait_time = 20 * (attempt + 1)
                        print(f"Rate limit for fallback ({model_name}). Waiting {wait_time}s to retry...")
                        time.sleep(wait_time)
                        continue # Retry same model
                    else:
                        print(f"Rate limit hit for {model_name}. Switching/Failing...")
                        break # Go to next model in outer loop
                else:
                    print(f"Error with {model_name}: {e}")
                    break # Non-rate limit error, try next model

    print("All Gemini models failed or rate limited.")
    return None

def find_timestamps_from_text(start_phrase, end_phrase, events):
    if not events: return None, None

    # Normalization function
    def clean(t): 
        # Remove special chars, extra spaces, lower case
        text = re.sub(r'[^\w\s]', '', t.lower())
        # Arabic Normalization
        text = re.sub(r'[أإآ]', 'ا', text) # Normalize Alefs
        text = re.sub(r'ة', 'ه', text)      # Normalize Taa Marbuta
        text = re.sub(r'ى', 'ي', text)      # Normalize Alef Maqsura
        text = re.sub(r'ؤ', 'و', text)      # Normalize Waw Hamza - optional but can help
        return re.sub(r'\s+', ' ', text).strip()

    start_phrase_clean = clean(start_phrase)
    end_phrase_clean = clean(end_phrase)
    
    print(f"  > Searching for Start: '{start_phrase_clean}'")
    print(f"  > Searching for End:   '{end_phrase_clean}'")

    # Build a full text string and a map from char index to event
    full_text = ""
    char_to_event_map = []
    
    for i, ev in enumerate(events):
        ev_text = clean(ev['text'])
        if not ev_text:
            continue
            
        # Add space separator if not start
        if full_text:
            full_text += " "
            char_to_event_map.append(None) # Gap
            
        start_idx = len(full_text)
        full_text += ev_text
        # Map every character in this segment to the event index
        char_to_event_map.extend([i] * len(ev_text))

    # Search
    start_time = None
    end_time = None
    
    # Fuzzy/Approx search for Start
    # Try exact first
    s_idx = full_text.find(start_phrase_clean)
    if s_idx != -1:
        # Found exact match
        # Map char index back to event
        # If it hits a gap (None), move forward
        while s_idx < len(char_to_event_map) and char_to_event_map[s_idx] is None:
            s_idx += 1
        
        if s_idx < len(char_to_event_map):
            ev_idx = char_to_event_map[s_idx]
            start_time = events[ev_idx]['start']
    else:
        # Fallback: Try matching first 20 chars
        short_start = start_phrase_clean[:20]
        if len(short_start) > 5:
            s_idx = full_text.find(short_start)
            if s_idx != -1:
                while s_idx < len(char_to_event_map) and char_to_event_map[s_idx] is None:
                    s_idx += 1
                if s_idx < len(char_to_event_map):
                    ev_idx = char_to_event_map[s_idx]
                    start_time = events[ev_idx]['start']

    # Search for End
    # Try exact
    e_idx = full_text.find(end_phrase_clean, s_idx if s_idx != -1 else 0)
    if e_idx != -1:
        # Map to event (end of phrase)
        end_char = e_idx + len(end_phrase_clean) - 1
        ensure_idx = min(end_char, len(char_to_event_map) - 1)
        
        while ensure_idx >= 0 and char_to_event_map[ensure_idx] is None:
            ensure_idx -= 1
            
        if ensure_idx >= 0:
            ev_idx = char_to_event_map[ensure_idx]
            end_time = events[ev_idx]['end']
    else:
         # Fallback: Try matching last 20 chars
        short_end = end_phrase_clean[-20:]
        if len(short_end) > 5:
            e_idx = full_text.find(short_end, s_idx if s_idx != -1 else 0)
            if e_idx != -1:
                end_char = e_idx + len(short_end) - 1
                ensure_idx = min(end_char, len(char_to_event_map) - 1)
                while ensure_idx >= 0 and char_to_event_map[ensure_idx] is None:
                    ensure_idx -= 1
                if ensure_idx >= 0:
                    ev_idx = char_to_event_map[ensure_idx]
                    end_time = events[ev_idx]['end']
    
    return start_time, end_time

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
                            s_phrase = analysis.get('start_phrase', '')
                            e_phrase = analysis.get('end_phrase', '')
                            print(f"  > Start Phrase: '{s_phrase}'")
                            print(f"  > End Phrase:   '{e_phrase}'")
                            
                            g_start, g_end = find_timestamps_from_text(s_phrase, e_phrase, window_subs)
                            print(f"  > Matched Times: {g_start} - {g_end}")
                            
                            if g_start is not None and g_end is not None:
                                duration = g_end - g_start
                                if duration < 5:
                                     print(f"  > Duration {duration}s too short.")
                                else:
                                    final_start = g_start
                                    final_end = g_end
                                    
                                    # Clamp to 60s if too long (Shorts limit)
                                    if duration > 60:
                                        print(f"  > Duration {duration}s exceeds limit. Clamping to 60s.")
                                        final_end = final_start + 60
                                    
                                    gemini_success = True
                            else:
                                print(f"  > Failed to match phrases in transcript.")
                
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

import os
import whisper
from moviepy.editor import VideoFileClip
import subprocess
import ass
from arabic_reshaper import reshape
from bidi.algorithm import get_display

def seconds_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS time format (H:MM:SS.CS)"""
    hours, remainder = divmod(seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    seconds, centiseconds = divmod(remainder, 1)
    return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}.{int(centiseconds*100):02d}"

def add_subtitles(video_path, model_size='large'):
    # Extract audio from video
    video = VideoFileClip(video_path)
    audio_path = "temp_audio.wav"
    video.audio.write_audiofile(audio_path, codec='pcm_s16le')

    # Transcribe audio with word-level timestamps
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, word_timestamps=True)
    detected_lang = result['language'].upper()

    # Create ASS document
    doc = ass.Document()
    arabic_style = ass.Style(
        name="Arabic",
        fontname="Arial",
        fontsize=24,
        bold=True,
        outline=3,
        shadow=2,
        alignment=2,  # Changed to bottom-center
        margin_v=40,   # Vertical margin from bottom
        encoding=1,
    )
    doc.styles.append(arabic_style)
    style_name = "Arabic"

    for segment in result['segments']:
        line_start = segment['start']
        line_end = segment['end']
        text_parts = []
        previous_end = line_start
        full_text = []

        words = segment.get('words', [])

        for word in words:
            if (gap := word['start'] - previous_end) > 0.01:
                text_parts.append(f"{{\\k{int(gap * 100)}}}")

            word_duration = word['end'] - word['start']
            word_text = word['word']

            # Process Arabic text
            if detected_lang == 'AR':
                reshaped = reshape(word_text)
                bidi_text = get_display(reshaped)
                full_text.append(bidi_text)
                # White text with black background and highlight
                text_parts.append(
                    f"{{\\k{int(word_duration * 100)}}}"
                    f"{{\\1c&HFFFFFF&\\3c&H000000&\\4a&H64&}}{bidi_text}"
                )
            previous_end = word['end']

        # RTL formatting
        if detected_lang == 'AR':
            full_line = ' '.join(full_text[::-1])
            reshaped_line = get_display(reshape(full_line))
            final_text = f"{{\\r}}{reshaped_line}"
        else:
            final_text = "".join(text_parts)

        # Add animated background for highlighting
        final_text = f"{{\\fad(300,300)}}{final_text}"

        doc.events.append(
            ass.Dialogue(
                start=seconds_to_ass_time(line_start),
                end=seconds_to_ass_time(line_end),
                style=style_name,
                text=final_text,
            )
        )

    # Save subtitles
    with open("temp_subs.ass", "w", encoding="utf-8") as f:
        doc.dump_file(f)

    # Burn subtitles into video
    output_path = video_path.replace(".", "_subtitled.")
    subprocess.run([
        'ffmpeg',
        '-i', video_path,
        '-vf', "ass=temp_subs.ass",
        '-c:a', 'copy',
        '-y',
        output_path
    ])

    # Cleanup
    os.remove(audio_path)
    os.remove("temp_subs.ass")

if __name__ == "__main__":
    video_file = "arabic_test.mp4"
    add_subtitles(video_file, model_size='base')
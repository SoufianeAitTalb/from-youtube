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
    return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}.{int(centiseconds * 100):02d}"


def add_subtitles(video_path, output_path, model_size='large'):
    # Convert video_path to absolute if not already
    video_path = os.path.abspath(video_path)
    output_path = os.path.abspath(output_path)

    # Extract audio from video
    video = VideoFileClip(video_path)
    audio_path = os.path.abspath("temp_audio.wav")
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
        fontsize=16,
        bold=True,
        outline=3,
        shadow=2,
        alignment=2,
        margin_v=40,
        encoding=1,
    )
    default_style = ass.Style(
        name="Default",
        fontname="Arial",
        fontsize=16,
        bold=True,
        outline=3,
        shadow=2,
        alignment=2,
        margin_v=40,
        encoding=0,
    )
    doc.styles.extend([arabic_style, default_style])
    style_name = "Arabic" if detected_lang == 'AR' else "Default"

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

            if detected_lang == 'AR':
                reshaped = reshape(word_text)
                bidi_text = get_display(reshaped)
                full_text.append(bidi_text)
                text_parts.append(
                    f"{{\\k{int(word_duration * 100)}}}"
                    f"{{\\1c&HFFFFFF&\\3c&H000000&\\4a&H64&}}{bidi_text}"
                )
            else:
                text_parts.append(
                    f"{{\\k{int(word_duration * 100)}}}{word_text}"
                )
            previous_end = word['end']

        if detected_lang == 'AR':
            full_line = ' '.join(full_text[::-1])
            reshaped_line = get_display(reshape(full_line))
            final_text = f"{{\\r}}{reshaped_line}"
        else:
            final_text = "".join(text_parts)

        final_text = f"{{\\fad(300,300)}}{final_text}"

        doc.events.append(
            ass.Dialogue(
                start=seconds_to_ass_time(line_start),
                end=seconds_to_ass_time(line_end),
                style=style_name,
                text=final_text,
            )
        )

    with open("temp_subs.ass", "w", encoding="utf-8") as f:
        doc.dump_file(f)

    subprocess.run([
        'ffmpeg',
        '-i', video_path,
        '-vf', "ass=temp_subs.ass",
        '-c:a', 'copy',
        '-y',
        output_path
    ])

    os.remove(audio_path)
    os.remove("temp_subs.ass")


def batch_process(input_dir, output_dir):
    input_dir = os.path.abspath(input_dir)
    output_dir = os.path.abspath(output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    video_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
    total_videos = len(video_files)

    print(f"Found {total_videos} videos to process")

    for idx, filename in enumerate(video_files, 1):
        input_path = os.path.join(input_dir, filename)
        base_name, ext = os.path.splitext(filename)
        output_filename = f"{base_name}_subtitled{ext}"  # Add _subtitled BEFORE extension
        output_path = os.path.join(output_dir, output_filename)
        print(f"\nProcessing video {idx}/{total_videos}: {filename}")
        add_subtitles(input_path, output_path,"medium")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(script_dir, "arabic_test.mp4")
    base_name, ext = os.path.splitext(os.path.basename(video_path))
    output_dir = os.path.join(script_dir, "subtitled")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{base_name}_subtitled{ext}")
    add_subtitles(video_path, output_path, model_size='base')
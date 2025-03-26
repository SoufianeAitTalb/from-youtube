import os
import whisper
from moviepy.editor import VideoFileClip
from pysubs2 import SSAFile, SSAEvent, SSAStyle
import subprocess

def add_subtitles(video_path, model_size='large'):
    # Extract audio from video
    video = VideoFileClip(video_path)
    audio_path = "temp_audio.wav"
    video.audio.write_audiofile(audio_path, codec='pcm_s16le')

    # Transcribe audio with word-level timestamps
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, word_timestamps=True)
    detected_lang = result['language'].upper()

    # Configure subtitle styling
    subs = SSAFile()
    subs.info.update({'PlayResX': '384', 'PlayResY': '288'})

    # Modern style parameters
    base_style = SSAStyle(
        fontsize=24,
        primarycolor="&H00FFFFFF",
        outlinecolor="&H00000000",
        backcolor="&HB0000000",  # Semi-transparent background
        bold=True,
        outline=3,
        shadow=2,
        alignment=2,  # Bottom-center
        marginv=40,
        fontname="Arial Unicode MS"  # Better Unicode support
    )

    # Arabic-specific adjustments
    if detected_lang == 'AR':
        arabic_style = base_style.copy()
        arabic_style.fontname = "Noto Naskh Arabic"
        arabic_style.encoding = 1
        arabic_style.alignment = 2  # Bottom-center
        arabic_style.marginv = 45
        subs.styles["Arabic"] = arabic_style
        style_name = "Arabic"
    else:
        subs.styles["Default"] = base_style
        style_name = "Default"

    # Process segments with proper RTL handling
    for segment in result['segments']:
        line_start = segment['start']
        line_end = segment['end']
        text_parts = []
        previous_end = line_start

        words = segment.get('words', [])

        # Reverse words for RTL languages to ensure correct display order
        if detected_lang == 'AR':
            words = list(reversed(words))

        for word in words:
            if (gap := word['start'] - previous_end) > 0.01:
                text_parts.append(f"{{\\k{int(gap * 100)}}}")

            word_duration = word['end'] - word['start']
            text_parts.append(f"{{\\k{int(word_duration * 100)}}}{word['word']}")
            previous_end = word['end']

        # Apply RTL formatting and modern styling
        if detected_lang == 'AR':
            final_text = "{\\rtl\\bord3\\shad2\\fs18}" + "".join(text_parts)
        else:
            final_text = "{\\bord3\\shad2\\fs24}" + "".join(text_parts)

        event = SSAEvent(
            start=int(line_start * 1000),
            end=int(line_end * 1000),
            text=final_text,
            style=style_name
        )
        subs.append(event)

    # Clean up any remaining 'tl' styles
    if 'tl' in subs.styles:
        del subs.styles['tl']

    # Save subtitles
    subs.save("temp_subs.ass")

    # Burn subtitles into video
    output_path = video_path.replace(".", "_subtitled.")
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', "ass=temp_subs.ass",
        '-c:a', 'copy',
        '-y',
        output_path
    ]
    subprocess.run(ffmpeg_cmd)

    # Cleanup
    os.remove(audio_path)
    os.remove("temp_subs.ass")

if __name__ == "__main__":
    video_file = "arabic_test.mp4"
    add_subtitles(video_file, model_size='base')
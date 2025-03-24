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

    # Base style for all languages
    base_style = SSAStyle(
        fontsize=20,
        primarycolor="&H00FFFFFF",
        outlinecolor="&H00000000",
        backcolor="&H80000000",
        bold=True,
        outline=2,
        shadow=0,
        alignment=8,  # Bottom-center
        marginv=35  # Position from bottom
    )

    # Arabic-specific adjustments
    if detected_lang == 'AR':
        arabic_style = base_style.copy()
        arabic_style.fontname = "Noto Naskh Arabic"  # Better Arabic support
        arabic_style.encoding = 1
        arabic_style.marginv = 40  # Bottom position
        subs.styles["Arabic"] = arabic_style
        style_name = "Arabic"
    else:
        base_style.fontname = "Arial"
        subs.styles["Default"] = base_style
        style_name = "Default"

    # Process segments with proper RTL handling
    for segment in result['segments']:
        line_start = segment['start']
        line_end = segment['end']
        text_parts = []
        previous_end = line_start

        words = segment['words']
        if detected_lang == 'AR':
            words = list(reversed(words))  # Reverse words for correct RTL display

        for word in words:
            if (gap := word['start'] - previous_end) > 0.01:
                text_parts.append(f"{{\\k{int(gap * 100)}}}")

            word_duration = word['end'] - word['start']
            text_parts.append(f"{{\\k{int(word_duration * 100)}}}{word['word']}")
            previous_end = word['end']

        # For Arabic: apply RTL tag to the entire line, not just the words
        if detected_lang == 'AR':
            final_text = "{\\rtl}" + "".join(text_parts)  # Ensure full line is in RTL
        else:
            final_text = "".join(text_parts)

        event = SSAEvent(
            start=int(line_start * 1000),
            end=int(line_end * 1000),
            text=final_text,
            style=style_name  # Ensure the style_name is correctly set to 'Arabic' or 'Default'
        )
        subs.append(event)

    # Clean up by removing unwanted styles if any (e.g., 'tl')
    for style in list(subs.styles):
        if style == 'tl':  # Explicitly remove any reference to 'tl'
            del subs.styles[style]

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
    video_file = "vertical_jiCezbNBNQE_part_1.mp4"
    add_subtitles(video_file, model_size='medium')  # You can choose between 'large', 'medium', 'base', 'tiny'

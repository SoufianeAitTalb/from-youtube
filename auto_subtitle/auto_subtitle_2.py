import os
import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from PIL import ImageFont
import numpy as np


def calculate_text_width(text, font_path='Arial.ttf', font_size=80):
    """Calculate text width using PIL"""
    font = ImageFont.truetype(font_path, font_size)
    return font.getlength(text)


def create_highlighted_subtitles(segment, video_size, is_rtl=False):
    """Create subtitle clips with word highlights"""
    video_width, video_height = video_size
    words = segment.get('words', [])
    if not words:
        return []

    # Create full text for the segment
    full_text = ' '.join([word['word'].strip() for word in words])

    # Reshape and directionize Arabic text
    # if is_rtl:
    #     full_text = get_display(reshape(full_text))

    # Create base text clip (white, full line)
    base_clip = TextClip(
        full_text,
        font='Arial.ttf',
        fontsize=80,
        color='white',
        size=(video_width - 50, None),
        method='caption',
        align='center'
    ).set_start(segment['start']).set_duration(segment['end'] - segment['start'])

    # Calculate vertical position
    y_position = video_height - 400
    base_clip = base_clip.set_position(('center', y_position))

    highlight_clips = [base_clip]

    # Create word highlight clips
    for word in words:
        word_text = word['word'].strip()
        start_time = word['start']
        end_time = word['end']

        # Calculate position of the word in the full text
        prefix = ' '.join([w['word'].strip() for w in words[:words.index(word)]])
        if is_rtl:
            prefix = ' '.join([w['word'].strip() for w in words[words.index(word) + 1:]])

        # Calculate widths using accurate measurements
        full_width = calculate_text_width(full_text)
        prefix_width = calculate_text_width(prefix + ' ') if prefix else 0
        word_width = calculate_text_width(word_text)

        # Calculate base text positioning accounting for container width
        container_width = video_width - 50
        text_x_offset = (container_width - full_width) // 2  # Center within subtitle area
        base_x_position = (video_width - container_width) // 2  # 25px padding

        # Final position calculation
        x_position = base_x_position + text_x_offset + prefix_width

        # Create highlight clip with precise positioning
        highlight_clip = TextClip(
            word_text,
            font='Arial.ttf',
            fontsize=80,
            color='yellow',
            size=(word_width, None),
            method='caption',
            align='East'  # Changed to left alignment for precise positioning
        ).set_start(start_time).set_duration(end_time - start_time)

        highlight_clip = highlight_clip.set_position((x_position, y_position))
        highlight_clips.append(highlight_clip)
    return highlight_clips


def add_subtitles(video_path, output_path, model_size='base'):
    video_path = os.path.abspath(video_path)
    output_path = os.path.abspath(output_path)

    # Load video
    video = VideoFileClip(video_path)
    video_size = video.size

    # Extract audio
    audio_path = "temp_audio.wav"
    video.audio.write_audiofile(audio_path, codec='pcm_s16le')

    # Transcribe audio
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, word_timestamps=True)
    detected_lang = result['language'].upper()
    is_rtl = detected_lang == 'AR'

    # Create subtitle clips
    subtitle_clips = []
    for segment in result['segments']:
        subtitle_clips.extend(create_highlighted_subtitles(segment, video_size, is_rtl))

    # Composite video with subtitles
    final_video = CompositeVideoClip([video] + subtitle_clips)

    # Write output
    final_video.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        threads=4,
        preset='medium',
        ffmpeg_params=['-crf', '23']
    )

    # Cleanup
    os.remove(audio_path)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(script_dir, "arabic_test.mp4")
    output_dir = os.path.join(script_dir, "subtitled")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(video_path).replace('.', '_subtitled.'))
    add_subtitles(video_path, output_path, model_size='base')
import os
import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from arabic_reshaper import reshape
from bidi.algorithm import get_display


def create_subtitle_clip(text, start, end, video_size, is_rtl=False):
    """Create a subtitle clip with proper positioning"""
    duration = end - start
    video_width, video_height = video_size

    # Reshape and directionize Arabic text
    # if is_rtl:
    #     text = get_display(reshape(text))

    # Create text clip with proper positioning
    txt_clip = TextClip(
        text,
        font='Arial',
        fontsize=40,
        color='white',
        bg_color='black',
        size=(video_width - 100, None),
        method='caption',
        align='center'
    ).set_start(start).set_duration(duration)

    # Calculate vertical position (50 pixels from bottom)
    y_position = video_height - 50
    return txt_clip.set_position(('center', y_position))


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
        words = segment.get('words', [])
        if not words:
            continue

        # Combine words into phrases
        full_text = ' '.join([word['word'].strip() for word in words])
        subtitle_clip = create_subtitle_clip(
            full_text,
            segment['start'],
            segment['end'],
            video_size,
            is_rtl
        )
        subtitle_clips.append(subtitle_clip)

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
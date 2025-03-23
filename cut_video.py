from moviepy.editor import VideoFileClip
import os


def cut_video(video_file,video_id, replayed_parts):
    # Create an output directory to save the parts
    output_dir = f"video_parts/{video_id}"
    os.makedirs(output_dir, exist_ok=True)

    for part in replayed_parts:
        start_time = part["start"]
        end_time = part["end"]

        # Correctly create the output filename without including the full video path
        output_filename = os.path.join(output_dir, f"part_{part['position']}.mp4")

        # Using moviepy to extract the part of the video
        try:
            video_clip = VideoFileClip(video_file).subclip(start_time, end_time)
            video_clip.write_videofile(output_filename, codec="libx264")
            print(f"Saved part {part['position']} as {output_filename}")
        except Exception as e:
            print(f"Error cutting video part {part['position']}: {e}")

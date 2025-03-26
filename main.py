import os.path

import auto_subtitle.auto_subtitle
from crop_video.crop_video_deep import batch_process
from cut_video import cut_video
from download_video import download_video
from replayed_parts import get_replayed_parts

# Main script
if __name__ == "__main__":
    video_id = "jiCezbNBNQE"  # Replace with the actual video ID
    number_of_parts = 3  # You can change this to get more parts

    # Step 1: Get the most replayed parts from the API
    replayed_parts = get_replayed_parts(video_id, number_of_parts)
    if not replayed_parts:
        print("No replayed parts found.")
    else:
        # Step 2: Download the full video from YouTube
        print("****************************************************part1:download video*********************************************")
        video_file = download_video(video_id,f"processing_output/downloaded_videos/{video_id}")
        if video_file:
            # Step 3: Cut the video into the replayed parts and save them
            print(
                "****************************************************part2:cutting video*********************************************")

            cut_video(video_file,video_id, replayed_parts,f"processing_output/video_parts/{video_id}")
            print(
                "****************************************************part3:cropping video*********************************************")
            batch_process(f"processing_output/video_parts/{video_id}",f"processing_output/cropped_video_parts/{video_id}")
            print(
                "****************************************************part4:adding subtitles*********************************************")
            auto_subtitle.auto_subtitle.batch_process(f"processing_output/cropped_video_parts/{video_id}",f"processing_output/subtitled_video_parts/{video_id}")

        else:
            print("Failed to download the video.")

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
        video_file = download_video(video_id)
        if video_file:
            # Step 3: Cut the video into the replayed parts and save them
            cut_video(video_file,video_id, replayed_parts)
        else:
            print("Failed to download the video.")

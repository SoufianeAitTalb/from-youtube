import cv2
import numpy as np
import os
import moviepy.editor as mpy


def process_video(input_path, output_path):
    # Load face detection model
    model_file = "res10_300x300_ssd_iter_140000_fp16.caffemodel"
    config_file = "deploy.prototxt"
    net = cv2.dnn.readNetFromCaffe(config_file, model_file)

    # Open input video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video {input_path}")
        return

    # Get video properties
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    filename = os.path.basename(input_path)

    # Calculate crop dimensions
    crop_width = int((9 / 16) * original_height)
    target_width, target_height = 1080, 1920

    # Create temporary video file (without audio)
    temp_output = "temp_video_no_audio.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (target_width, target_height))

    # Smoothing parameters for face tracking
    prev_crop_x = (original_width - crop_width) // 2
    smoothing_factor = 0.2

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        percent = (frame_count / total_frames) * 100
        print(f"\rProcessing {filename}: {percent:.1f}%", end='', flush=True)

        # Face detection
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        best_face = None
        max_confidence = 0.5

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > max_confidence:
                max_confidence = confidence
                box = detections[0, 0, i, 3:7] * np.array([original_width, original_height,
                                                           original_width, original_height])
                (startX, startY, endX, endY) = box.astype("int")
                best_face = (startX, startY, endX, endY)

        # Calculate crop position
        if best_face:
            face_center_x = (best_face[0] + best_face[2]) // 2
            desired_crop_x = face_center_x - crop_width // 2
            desired_crop_x = max(0, min(desired_crop_x, original_width - crop_width))

            # Apply smoothing
            crop_x = int(prev_crop_x * (1 - smoothing_factor) + desired_crop_x * smoothing_factor)
            prev_crop_x = crop_x
        else:
            crop_x = prev_crop_x

        # Crop and resize
        cropped = frame[0:original_height, int(crop_x):int(crop_x + crop_width)]
        resized = cv2.resize(cropped, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
        out.write(resized)

    cap.release()
    out.release()
    print(f"\r{filename}: Video processing complete (100.0%)")

    # Add audio to final output
    try:
        video = mpy.VideoFileClip(temp_output)
        audio = mpy.AudioFileClip(input_path)
        final = video.set_audio(audio)
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        video.close()
        audio.close()
        os.remove(temp_output)
        print(f"{filename}: Audio added successfully")
    except Exception as e:
        print(f"\nError processing audio: {str(e)}")


def batch_process(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    video_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
    total_videos = len(video_files)

    print(f"Found {total_videos} videos to process")

    for idx, filename in enumerate(video_files, 1):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, f"vertical_{filename}")
        print(f"\nProcessing video {idx}/{total_videos}: {filename}")
        process_video(input_path, output_path)


if __name__ == "__main__":
    input_directory = "./"
    output_directory = "output_videos"

    # Check for required files
    if not all(os.path.exists(f) for f in ["deploy.prototxt", "res10_300x300_ssd_iter_140000_fp16.caffemodel"]):
        print("Missing face detection models. Download:")
        print("https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt")
        print(
            "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel")
        exit()

    # Check for moviepy
    try:
        import moviepy
    except ImportError:
        print("Installing required MoviePy package...")
        os.system("pip install moviepy")
        import moviepy

    batch_process(input_directory, output_directory)
    print("\nAll videos processed successfully!")
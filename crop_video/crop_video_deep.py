import cv2
import numpy as np
import os


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

    # Calculate crop dimensions
    crop_width = int((9 / 16) * original_height)
    target_width = 1080
    target_height = 1920

    # Video writer setup
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (target_width, target_height))

    # Smoothing parameters for face tracking
    prev_crop_x = (original_width - crop_width) // 2
    smoothing_factor = 0.2

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        progress = f"Processing frame {frame_count}/{total_frames} ({(frame_count / total_frames) * 100:.2f}%) of {os.path.basename(input_path)}"
        print(progress, end='\r', flush=True)  # Ensure the progress is flushed

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

        # Write output
        out.write(resized)

    cap.release()
    out.release()
    print(f"\nFinished processing video {os.path.basename(input_path)}")


def batch_process(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    total_files = len([f for f in os.listdir(input_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))])
    processed_files = 0

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.mp4', '.avi', '.mov')):

            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"vertical_{filename}")
            processed_files += 1

            print(f"\nProcessing {filename} ({processed_files}/{total_files})...")
            process_video(input_path, output_path)

    print(f"\nFinished processing all videos in {input_dir}")


if __name__ == "__main__":
    input_directory = "./"
    output_directory = "output_videos"

    # Download required face detection models if missing
    if not os.path.exists("deploy.prototxt") or not os.path.exists("res10_300x300_ssd_iter_140000_fp16.caffemodel"):
        print("Error: Face detection models missing. Please download:")
        print("https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt")
        print(
            "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel")
        exit()

    batch_process(input_directory, output_directory)

import cv2
import numpy as np
import os
from collections import deque
import moviepy.editor as mpy


class ResponsiveKalmanFilter:
    def __init__(self, process_var=1e-4, measure_var=0.1 ** 2):
        self.process_var = process_var
        self.measure_var = measure_var
        self.state_estimate = None
        self.estimate_error = 1.0

    def update(self, measurement):
        if self.state_estimate is None:
            self.state_estimate = measurement
            return self.state_estimate

        # More responsive prediction update
        pred_error = self.estimate_error + self.process_var

        # Higher Kalman gain for quicker response
        kalman_gain = pred_error / (pred_error + self.measure_var)
        self.state_estimate = self.state_estimate + kalman_gain * (measurement - self.state_estimate)
        self.estimate_error = (1 - kalman_gain) * pred_error

        return self.state_estimate


def process_video(input_path, output_path):
    # Load face detection model
    model_file = "res10_300x300_ssd_iter_140000_fp16.caffemodel"
    config_file = "deploy.prototxt"
    net = cv2.dnn.readNetFromCaffe(config_file, model_file)

    # Initialize more responsive Kalman Filters
    kf_x = ResponsiveKalmanFilter(process_var=1e-4, measure_var=0.3 ** 2)
    kf_y = ResponsiveKalmanFilter(process_var=1e-4, measure_var=0.3 ** 2)

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

    # Calculate dimensions
    crop_width = int((9 / 16) * original_height)
    target_width, target_height = 1080, 1920

    # Video writer (temporary file)
    temp_output = "temp_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (target_width, target_height))

    # More responsive smoothing parameters
    buffer_size = 12  # Reduced from 20 to 12
    x_buffer = deque(maxlen=buffer_size)
    prev_crop_x = (original_width - crop_width) // 2

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        percent_complete = (frame_count / total_frames) * 100
        print(f"\rProcessing {filename}: {percent_complete:.1f}%", end='', flush=True)

        # More frequent face detection (every 2 frames)
        face_center = None
        if frame_count % 2 == 1:  # Increased detection frequency
            blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104.0, 177.0, 123.0))
            net.setInput(blob)
            detections = net.forward()

            max_confidence = 0.4  # Lower confidence threshold
            best_face = None

            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > max_confidence:
                    max_confidence = confidence
                    box = detections[0, 0, i, 3:7] * np.array([original_width, original_height,
                                                               original_width, original_height])
                    (startX, startY, endX, endY) = box.astype("int")
                    best_face = (startX, startY, endX, endY)

            if best_face:
                face_center_x = (best_face[0] + best_face[2]) // 2
                face_center_y = (best_face[1] + best_face[3]) // 2
                face_center = (kf_x.update(face_center_x), kf_y.update(face_center_y))

        # Calculate crop position with faster response
        if face_center:
            desired_crop_x = face_center[0] - crop_width // 2
            # Tighter boundaries with 5% margin
            max_crop = original_width - crop_width
            desired_crop_x = np.clip(desired_crop_x, max_crop * 0.05, max_crop * 0.95)
            x_buffer.append(desired_crop_x)
        else:
            x_buffer.append(prev_crop_x)

        # Use exponential moving average for faster response
        alpha = 0.3  # Higher alpha weights recent values more heavily
        if len(x_buffer) > 1:
            smooth_crop_x = x_buffer[-1] * alpha + (1 - alpha) * np.mean(x_buffer)
        else:
            smooth_crop_x = x_buffer[0] if x_buffer else prev_crop_x

        smooth_crop_x = int(np.clip(smooth_crop_x, 0, original_width - crop_width))
        prev_crop_x = smooth_crop_x

        # Crop and resize
        cropped = frame[0:original_height, smooth_crop_x:smooth_crop_x + crop_width]
        resized = cv2.resize(cropped, (target_width, target_height), interpolation=cv2.INTER_CUBIC)

        # Write output
        out.write(resized)

    cap.release()
    out.release()
    print(f"\r{filename}: Processed {frame_count} frames (100.0%)   ")

    # Add audio to final output
    try:
        video_clip = mpy.VideoFileClip(temp_output)
        audio_clip = mpy.AudioFileClip(input_path)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        video_clip.close()
        audio_clip.close()
        os.remove(temp_output)
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
        print(f"\nStarting video {idx}/{total_videos}: {filename}")
        process_video(input_path, output_path)


if __name__ == "__main__":
    input_directory = "./"
    output_directory = "output_videos"

    # Check for face detection models
    if not all(os.path.exists(f) for f in ["deploy.prototxt", "res10_300x300_ssd_iter_140000_fp16.caffemodel"]):
        print("Error: Missing face detection models. Please download:")
        print("https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt")
        print(
            "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel")
        exit()

    # Install required packages if missing
    try:
        import moviepy
    except ImportError:
        print("\nInstalling required MoviePy package...")
        os.system("pip install moviepy")

    batch_process(input_directory, output_directory)
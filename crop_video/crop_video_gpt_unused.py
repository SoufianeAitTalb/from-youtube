import cv2
import numpy as np

# Load the pre-trained Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def process_frame(frame, frame_width, frame_height):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) > 0:
        # Assume the first detected face is the speaker
        x, y, w, h = faces[0]

        # Calculate the center of the face
        face_center_x = x + w // 2
        face_center_y = y + h // 2

        # Desired aspect ratio 9:16
        aspect_ratio = 9 / 16
        crop_width = frame_height * aspect_ratio  # Based on height for 9:16 aspect ratio
        crop_height = frame_height  # Maintain original height

        # Calculate crop coordinates centered on the face
        crop_x1 = face_center_x - crop_width // 2
        crop_x2 = face_center_x + crop_width // 2
        crop_y1 = 0
        crop_y2 = frame_height

        # Ensure the crop coordinates are within the video dimensions
        crop_x1 = int(max(0, crop_x1))  # Convert to integer
        crop_x2 = int(min(frame_width, crop_x2))  # Convert to integer
        crop_y1 = int(max(0, crop_y1))  # Convert to integer
        crop_y2 = int(min(frame_height, crop_y2))  # Convert to integer

        # Crop and resize the frame to fit the 9:16 aspect ratio
        cropped_frame = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        resized_frame = cv2.resize(cropped_frame, (frame_width, frame_height))  # Resize to match original resolution

        return resized_frame
    else:
        # If no face is detected, return the original frame
        return frame

def process_video(input_video_path, output_video_path):
    # Open the input video file
    cap = cv2.VideoCapture(input_video_path)

    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Get total number of frames for progress tracking
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Define codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 'mp4v' codec (fallback to this if 'XVID' doesn't work)
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Process the frame
        processed_frame = process_frame(frame, frame_width, frame_height)

        # Write the processed frame to the output video
        out.write(processed_frame)

        # Update the frame count and print progress
        frame_count += 1
        progress = (frame_count / total_frames) * 100
        print(f"Processing: {frame_count}/{total_frames} frames ({progress:.2f}%)")

    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    input_video = 'part_1.mp4'  # Input video file
    output_video = 'output_video.mp4'  # Output video file
    process_video(input_video, output_video)

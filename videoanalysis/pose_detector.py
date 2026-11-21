# pose_detector.py


import os
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# Load pose landmarker model
model_path = os.path.join(os.path.dirname(__file__), "pose_landmarker_full.task")
base_options = python.BaseOptions(
    model_asset_path=model_path
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=False
)

# Create detector once (important for performance)
detector = vision.PoseLandmarker.create_from_options(options)


def detect_pose(frame):

    # Convert BGR → RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to MediaPipe image
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    # Detect pose
    result = detector.detect(mp_image)

    # No person detected
    if not result.pose_landmarks:
        return None

    # Return first person landmarks
    return result.pose_landmarks[0]
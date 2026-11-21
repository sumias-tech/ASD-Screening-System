# video_processor.py

import cv2
from .pose_detector import detect_pose
from .scoring import calculate_score, reset_tracking


def process_video(video_path):

    reset_tracking()

    cap = cv2.VideoCapture(video_path)

    results = []
    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if frame_count % 5 == 0:

            landmarks = detect_pose(frame)

            if landmarks is not None:
                score = calculate_score(landmarks)
                results.append(score)

        frame_count += 1

    cap.release()

    if len(results) == 0:
        return {
            "eye_contact": 0,
            "attention": 0,
            "movement": 0,
            "asd_score": 0,
            "risk": "Unknown",
            "frames": 0,
            "eye_scores": [],
            "attention_scores": [],
            "movement_scores": [],
            "face_summary": "No measurable face direction data was available.",
            "head_summary": "No measurable head pose data was available.",
            "posture_summary": "No measurable body posture data was available.",
            "attention_summary": "No measurable attention data was available.",
            "eye_alignment_summary": "Eye alignment could not be assessed from this video.",
            "repetitive_summary": "No repetitive behavior summary is available.",
            "overall_summary": "The video did not contain enough usable frames for a reliable assessment."
        }

    avg_eye = sum(r["eye_contact"] for r in results) / len(results)
    avg_attention = sum(r["attention"] for r in results) / len(results)
    avg_movement = sum(r["movement"] for r in results) / len(results)

    final_score = (avg_eye + avg_attention + avg_movement) / 3

    if final_score >= 70:
        risk = "High"
    elif final_score >= 40:
        risk = "Moderate"
    else:
        risk = "Low"

    def _phrase(value, positive=True):
        if value >= 75:
            return "well maintained / consistent"
        if value >= 40:
            return "generally good with some variation"
        return "needs attention / frequently varies"

    face_summary = (
        "Your child’s face is mostly oriented towards the interaction/activity. "
        "This indicates good engagement with the surroundings."
        if avg_eye >= 75 else
        "Face orientation is generally good with some variation. Occasional moments of looking away were present."
        if avg_eye >= 40 else
        "Face direction varied at times and may need gentle monitoring, as the gaze shifted away from the main interaction."
    )

    head_summary = (
        "Head position appears stable and natural for most of the session."
        if avg_attention >= 75 else
        "Head position is generally natural, with some brief movements away from the interaction."
        if avg_attention >= 40 else
        "Head pose showed more frequent movement away from the interaction and may benefit from closer observation."
    )

    posture_summary = (
        "Your child maintains a comfortable and balanced posture."
        if avg_movement >= 75 else
        "Body posture is generally balanced, with some minor shifts during the video."
        if avg_movement >= 40 else
        "Posture varied more often and may need monitoring for repetitive or restless movement."
    )

    attention_summary = (
        "Your child is able to stay focused for most of the time."
        if avg_attention >= 75 else
        "Your child shows generally good focus with some variation during the session."
        if avg_attention >= 40 else
        "Attention varied frequently and may need gentle redirection to maintain engagement."
    )

    eye_alignment_summary = (
        "Eye alignment appears well-coordinated and consistent. This supports healthy visual attention and interaction."
        if avg_eye >= 75 and avg_attention >= 75 else
        "Eye alignment is generally good with some variation in direction and head pose."
        if avg_eye >= 40 or avg_attention >= 40 else
        "Eye alignment appears inconsistent and may need further observation."
    )

    repetitive_summary = (
        "No continuous repetitive behaviors were observed."
        if avg_movement >= 75 else
        "Some repetitive behaviors were noticed during certain parts of the session, such as hand/finger movements or brief head/leg gestures. These behaviors were not continuous and can be monitored."
        if avg_movement >= 40 else
        "Repetitive behaviors were noticed more often, including hand/finger movements and brief head/leg gestures. They appeared occasionally and may benefit from gentle redirection."
    )

    overall_summary = (
        "Based on the video analysis, your child shows generally positive engagement and interaction during the session. "
        "Some behaviors were observed that may need gentle monitoring, but they are not dominant."
        if risk == "Low" else
        "Based on the video analysis, your child shows moderate variation in behavior. Gentle monitoring and supportive activities may help improve engagement."
        if risk == "Moderate" else
        "Based on the video analysis, several behaviors were noted that may require closer attention. A specialist consultation is recommended for further guidance."
    )

    return {
        "eye_contact": round(avg_eye, 2),
        "attention": round(avg_attention, 2),
        "movement": round(avg_movement, 2),
        "asd_score": round(final_score, 2),
        "risk": risk,
        "frames": len(results),

        "eye_scores": [r["eye_contact"] for r in results],
        "attention_scores": [r["attention"] for r in results],
        "movement_scores": [r["movement"] for r in results],

        "face_summary": face_summary,
        "head_summary": head_summary,
        "posture_summary": posture_summary,
        "attention_summary": attention_summary,
        "eye_alignment_summary": eye_alignment_summary,
        "repetitive_summary": repetitive_summary,
        "overall_summary": overall_summary,
        "face_level": _phrase(avg_eye),
        "head_level": _phrase(avg_attention),
        "posture_level": _phrase(avg_movement),
        "attention_level": _phrase(avg_attention),
        "repetitive_level": _phrase(avg_movement),
    }
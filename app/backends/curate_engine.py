import os
import sys
import argparse
import glob
import cv2
import json
import uuid
import subprocess
from PIL import Image
import imagehash
from deepface import DeepFace

# Set strict device placement to GPU 1 (RTX 3060)
os.environ["CUDA_VISIBLE_DEVICES"] = "1"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", type=str, default="/app/media_ingest")
    parser.add_argument("--strictness", type=int, default=50)
    parser.add_argument("--pacing", type=float, default=3.0)
    parser.add_argument("--output_path", type=str, required=True)
    return parser.parse_args()

def calculate_sharpness(img_path_or_frame):
    # If image path
    if isinstance(img_path_or_frame, str):
        img = cv2.imread(img_path_or_frame)
    else:
        img = img_path_or_frame
        
    if img is None:
        return 0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def check_emotion_and_face(img_path_or_frame):
    # Returns (is_happy, score)
    try:
        # DeepFace analyze
        actions = ['emotion']
        res = DeepFace.analyze(img_path_or_frame, actions=actions, enforce_detection=True, silent=True)
        if isinstance(res, list) and len(res) > 0:
            face_data = res[0]
            emotions = face_data.get("emotion", {})
            happy_score = emotions.get("happy", 0.0)
            dominant = face_data.get("dominant_emotion", "")
            # Return true if happy is high or dominant is happy
            if dominant == "happy" or happy_score > 50.0:
                return True, happy_score
        return False, 0.0
    except Exception:
        # No face detected
        return False, 0.0

def process_video_file(video_path, clarity_thresh, temp_dir):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    # Extract 1 frame every 2 seconds, max 15 frames
    interval_seconds = 2
    frame_step = int(fps * interval_seconds)
    if frame_step <= 0:
        frame_step = 50

    frames_to_check = []
    curr_frame_idx = 0
    while curr_frame_idx < total_frames and len(frames_to_check) < 15:
        frames_to_check.append(curr_frame_idx)
        curr_frame_idx += frame_step

    candidates = []
    for f_idx in frames_to_check:
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        
        # 1. Clarity Check
        sharpness = calculate_sharpness(frame)
        if sharpness < clarity_thresh:
            continue

        # 2. Face / Emotion Check
        is_happy, emotion_score = check_emotion_and_face(frame)
        if not is_happy:
            continue

        # Save candidate frame to temp file to compute phash
        timestamp = f_idx / fps
        temp_img_path = os.path.join(temp_dir, f"vid_{uuid.uuid4().hex}.jpg")
        cv2.imwrite(temp_img_path, frame)
        
        try:
            with Image.open(temp_img_path) as pil_img:
                phash = imagehash.phash(pil_img)
        except Exception:
            phash = None

        candidates.append({
            "type": "video",
            "source": video_path,
            "timestamp": timestamp,
            "sharpness": sharpness,
            "emotion_score": emotion_score,
            "score": sharpness + emotion_score,
            "temp_img": temp_img_path,
            "phash": phash
        })
    cap.release()
    return candidates

def process_image_file(image_path, clarity_thresh, temp_dir):
    sharpness = calculate_sharpness(image_path)
    if sharpness < clarity_thresh:
        return None

    is_happy, emotion_score = check_emotion_and_face(image_path)
    if not is_happy:
        return None

    try:
        with Image.open(image_path) as pil_img:
            phash = imagehash.phash(pil_img)
    except Exception:
        phash = None

    return {
        "type": "image",
        "source": image_path,
        "sharpness": sharpness,
        "emotion_score": emotion_score,
        "score": sharpness + emotion_score,
        "temp_img": image_path,
        "phash": phash
    }

def main():
    args = parse_args()
    
    # Establish thresholds based on strictness
    # clarity threshold ranges from 10 to 150
    clarity_thresh = 10 + (args.strictness * 1.4)
    
    # Create temp dir for frame extractions
    temp_dir = f"/tmp/curate_{uuid.uuid4().hex}"
    os.makedirs(temp_dir, exist_ok=True)

    # Search for files in source dir
    media_extensions = ["*.jpg", "*.jpeg", "*.png", "*.mp4", "*.mkv", "*.mov", "*.avi"]
    all_files = []
    for ext in media_extensions:
        all_files.extend(glob.glob(os.path.join(args.source_dir, ext)))
        all_files.extend(glob.glob(os.path.join(args.source_dir, ext.upper())))

    all_files = sorted(list(set(all_files)))
    print(f"Found {len(all_files)} total media files to process.")

    candidates = []
    for file_path in all_files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".mp4", ".mkv", ".mov", ".avi"]:
            candidates.extend(process_video_file(file_path, clarity_thresh, temp_dir))
        else:
            cand = process_image_file(file_path, clarity_thresh, temp_dir)
            if cand:
                candidates.append(cand)

    print(f"Filters passed: {len(candidates)} candidates remain.")

    # Deduplication using pHash (>90% similarity means hash distance <= 4)
    unique_candidates = []
    for cand in sorted(candidates, key=lambda x: x["score"], reverse=True):
        if cand["phash"] is None:
            unique_candidates.append(cand)
            continue
        
        is_duplicate = False
        for unique in unique_candidates:
            if unique["phash"] is not None:
                distance = cand["phash"] - unique["phash"]
                if distance <= 4: # Duplicate found
                    is_duplicate = True
                    break
        if not is_duplicate:
            unique_candidates.append(cand)

    print(f"Deduplication completed. {len(unique_candidates)} unique assets selected.")

    if not unique_candidates:
        print("No media qualified for highlight reel.")
        sys.exit(0)

    # Assembly with FFmpeg
    # 1. Create short clips for each selected candidate
    clips = []
    for index, cand in enumerate(unique_candidates):
        clip_path = os.path.join(temp_dir, f"clip_{index}.mp4")
        if cand["type"] == "image":
            # Image to video loop of pacing length
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", cand["source"],
                "-t", str(args.pacing), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                clip_path
            ]
        else:
            # Video segment extraction starting at max(0, timestamp - 0.5s) for pacing length
            start_time = max(0.0, cand["timestamp"] - 0.5)
            cmd = [
                "ffmpeg", "-y", "-ss", str(start_time), "-i", cand["source"],
                "-t", str(args.pacing), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                "-an", clip_path # remove audio to prevent concat audio stream mismatches
            ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(clip_path):
            clips.append(clip_path)

    # 2. Concat all clips using ffmpeg concat demuxer
    if not clips:
        print("Failed to generate clips.")
        sys.exit(1)

    concat_txt_path = os.path.join(temp_dir, "concat.txt")
    with open(concat_txt_path, "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")

    # Final stitch command
    stitch_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", args.output_path
    ]
    
    print("Stitching highlight reel with FFmpeg...")
    res = subprocess.run(stitch_cmd)
    if res.returncode == 0:
        print(f"Successfully created highlight reel at: {args.output_path}")
    else:
        print("FFmpeg stitch command failed.")

    # Cleanup temp directory
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except Exception:
        pass

if __name__ == "__main__":
    main()

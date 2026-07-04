import os
import random
import uuid
import datetime

# Mock scheduled database
SCHEDULED_QUEUE = [
    {
        "publish_id": "pub-101",
        "title": "Spark AI Tutorial - Getting Started",
        "scheduled_time": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat(),
        "status": "scheduled",
        "platform": "youtube"
    },
    {
        "publish_id": "pub-102",
        "title": "Unlocking ComfyUI Consistency Secrets",
        "scheduled_time": (datetime.datetime.now() + datetime.timedelta(days=3)).isoformat(),
        "status": "scheduled",
        "platform": "youtube"
    }
]

async def generate_metadata(title: str, description: str, tags: list):
    """Generates standard Youtube publishing metadata bundle."""
    return {
        "title": title[:100],
        "description": f"{description}\n\n[Sponsored / Disclosures]\nProduced automatically by Spark AI Factory.",
        "tags": tags[:30],
        "category_id": "27",  # Education
        "status": "draft",
        "generated_at": datetime.datetime.now().isoformat()
    }

async def upload_video(file_path: str, metadata: dict):
    """Simulates a chunked resumable upload to Youtube and returns a mock Video ID."""
    # Convert absolute host path to relative path unconditionally
    if file_path:
        prefixes = ["/home/pkkumar/AGGY/spark-test-tool/", "/home/pkkumar/AGGY/spark-test-tool"]
        cwd = os.getcwd()
        prefixes.extend([cwd + "/", cwd])
        for prefix in prefixes:
            if file_path.startswith(prefix):
                file_path = file_path[len(prefix):].lstrip("/")
                break

    if not file_path or not os.path.exists(file_path):
         # If no actual file, check if it's a mock string or dummy path
         if not file_path.startswith("mock_"):
             raise FileNotFoundError(f"Video file not found at: {file_path}")

    # Simulate random mock YouTube Video ID
    video_id = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", k=11))
    
    return {
        "status": "success",
        "platform": "youtube",
        "video_id": video_id,
        "watch_url": f"https://www.youtube.com/watch?v={video_id}",
        "uploaded_at": datetime.datetime.now().isoformat(),
        "metadata": metadata
    }

async def get_schedule():
    """Retrieve queue of scheduled releases."""
    return {"queue": SCHEDULED_QUEUE}

async def schedule_video(title: str, publish_time: str):
    """Schedule a new upload release."""
    new_event = {
        "publish_id": f"pub-{uuid.uuid4().hex[:6]}",
        "title": title,
        "scheduled_time": publish_time,
        "status": "scheduled",
        "platform": "youtube"
    }
    SCHEDULED_QUEUE.append(new_event)
    return new_event

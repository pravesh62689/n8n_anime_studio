"""Test stable-video-diffusion space for video generation."""
import os, sys, time, shutil
from gradio_client import Client, handle_file

print("Connecting to multimodalart/stable-video-diffusion...")
try:
    client = Client("multimodalart/stable-video-diffusion")
    print("Connected. Launching /video job...")
    
    start_time = time.time()
    # image, seed, randomize_seed, motion_bucket_id, fps_id
    res = client.predict(
        image=handle_file("flux_base_test.png"),
        seed=42.0,
        randomize_seed=True,
        motion_bucket_id=127,
        fps_id=6,
        api_name="/video"
    )
    elapsed = time.time() - start_time
    print(f"Generated video in {elapsed:.2f}s!")
    print(f"Result: {res}")
    
    video_data = res[0]
    if isinstance(video_data, dict) and "video" in video_data:
        vid_path = video_data["video"]
        if os.path.exists(vid_path):
            shutil.copy(vid_path, "svd_motion_test.mp4")
            print(f"SUCCESS: Video saved to svd_motion_test.mp4 ({os.path.getsize('svd_motion_test.mp4')} bytes)")
except Exception as e:
    print(f"Failed to generate: {e}")

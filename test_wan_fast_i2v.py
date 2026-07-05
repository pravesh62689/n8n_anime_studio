"""Test multimodalart/wan2-1-fast space for fast I2V motion video generation."""
import os, sys, time, urllib.parse, shutil
from gradio_client import Client, handle_file
import httpx

print("1. Using assets/test_last_frame.png as base image...")
img_path = "assets/test_last_frame.png"
if not os.path.exists(img_path):
    print(f"Error: {img_path} does not exist.")
    sys.exit(1)

print("\n2. Connecting to multimodalart/wan2-1-fast...")
try:
    client = Client("multimodalart/wan2-1-fast")
    print("Connected. Initiating /generate_video job...")
    
    start_time = time.time()
    # input_image, prompt, height, width, negative_prompt, duration_seconds, guidance_scale, steps, seed, randomize_seed
    result = client.predict(
        input_image=handle_file(img_path),
        prompt="the cute anime cat is jumping and playing with the red ball, looking happy, dynamic animation, high quality, 2d motion",
        height=512,
        width=896,
        negative_prompt="Bright tones, static, blurred details, subtitles",
        duration_seconds=2,
        guidance_scale=1.0,
        steps=4,
        seed=42,
        randomize_seed=True,
        api_name="/generate_video"
    )
    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.2f}s!")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    # Check if a video path was returned
    if isinstance(result, tuple) and len(result) > 0:
        video_data = result[0]
        if isinstance(video_data, dict) and "video" in video_data:
            vid_path = video_data["video"]
            if os.path.exists(vid_path):
                dest = "test_wan_fast_i2v.mp4"
                shutil.copy(vid_path, dest)
                print(f"SUCCESS: Video saved to {dest} ({os.path.getsize(dest)} bytes)")
except Exception as e:
    print(f"Error during video generation: {e}")

"""Test chaining FLUX.1-schnell and Wan2.1-fast to generate a motion video clip."""
import os, sys, time, shutil
from gradio_client import Client, handle_file

print("1. Connecting to black-forest-labs/FLUX.1-schnell...")
try:
    flux_client = Client("black-forest-labs/FLUX.1-schnell")
    print("Generating base image using FLUX.1-schnell...")
    start_time = time.time()
    
    # prompt, seed, randomize_seed, width, height, num_inference_steps
    res = flux_client.predict(
        prompt="a cute anime cat playing with a red ball in a sunny garden, ghibli style, detailed, vibrant colors",
        seed=42.0,
        randomize_seed=True,
        width=896,
        height=512,
        num_inference_steps=4,
        api_name="/infer"
    )
    elapsed = time.time() - start_time
    print(f"Base image generated in {elapsed:.2f}s!")
    
    img_data = res[0]
    if isinstance(img_data, str):
        img_path = img_data
    elif isinstance(img_data, dict):
        img_path = img_data.get("path")
    else:
        img_path = None
        
    if not img_path or not os.path.exists(img_path):
        print(f"Error: generated image path {img_path} not found.")
        sys.exit(1)
        
    print(f"Generated base image path: {img_path} ({os.path.getsize(img_path)} bytes)")
    shutil.copy(img_path, "flux_base_test.png")
    
except Exception as e:
    print(f"FLUX generation failed: {e}")
    sys.exit(1)

print("\n2. Connecting to multimodalart/wan2-1-fast...")
try:
    wan_client = Client("multimodalart/wan2-1-fast")
    print("Generating motion video clip using wan2-1-fast...")
    start_time = time.time()
    
    # input_image, prompt, height, width, negative_prompt, duration_seconds, guidance_scale, steps, seed, randomize_seed
    res = wan_client.predict(
        input_image=handle_file("flux_base_test.png"),
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
    print(f"Motion video generated in {elapsed:.2f}s!")
    
    video_data = res[0]
    if isinstance(video_data, dict) and "video" in video_data:
        vid_path = video_data["video"]
        if os.path.exists(vid_path):
            shutil.copy(vid_path, "flux_wan_motion_test.mp4")
            print(f"SUCCESS: Video saved to flux_wan_motion_test.mp4 ({os.path.getsize('flux_wan_motion_test.mp4')} bytes)")
            
except Exception as e:
    print(f"Wan generation failed: {e}")

"""Test CogVideoX-5B-Space for motion video generation."""
import os, sys, time, shutil
os.environ["OMP_NUM_THREADS"] = "1"

from gradio_client import Client

PROMPT = "a cute anime cat walking through a magical forest, colorful butterflies flying around, children cartoon style, high quality animation"

print("="*60)
print("CogVideoX-5B-Space Test")
print("="*60)

try:
    client = Client("THUDM/CogVideoX-5B-Space")
    
    # CogVideoX /generate requires image_input and video_input but they may accept None
    # Try text-only first by passing empty/None values
    start = time.time()
    
    # Try with None/empty inputs
    try:
        print("[Test] Trying /generate with text prompt only...")
        result = client.predict(
            prompt=PROMPT,
            image_input=None,
            video_input=None,
            video_strength=0.8,
            seed_value=-1.0,
            scale_status=False,
            rife_status=False,
            api_name="/generate"
        )
        elapsed = time.time() - start
        print(f"[Test] Result in {elapsed:.1f}s: {result}")
        print(f"[Test] Type: {type(result)}")
        
        if isinstance(result, (list, tuple)):
            for i, item in enumerate(result):
                print(f"  Item[{i}]: {type(item)} = {item}")
                if isinstance(item, dict) and "video" in item:
                    vid = item["video"]
                    if os.path.exists(vid):
                        size = os.path.getsize(vid)
                        print(f"    >>> VIDEO FILE! {size} bytes")
                        shutil.copy(vid, "assets/test_cogvideo_motion.mp4")
                        print(f"    >>> Saved to assets/test_cogvideo_motion.mp4")
                elif isinstance(item, str) and os.path.exists(item):
                    size = os.path.getsize(item)
                    print(f"    >>> FILE! {size} bytes")
                    shutil.copy(item, "assets/test_cogvideo_motion.mp4")
    except Exception as e:
        print(f"[Test] /generate failed: {e}")
        
        # Try enhance_prompt_func
        print("\n[Test] Trying /enhance_prompt_func...")
        try:
            enhanced = client.predict(prompt=PROMPT, api_name="/enhance_prompt_func")
            print(f"[Test] Enhanced prompt: {enhanced}")
        except Exception as e2:
            print(f"[Test] enhance failed: {e2}")

except Exception as e:
    print(f"[Test] Space connection failed: {e}")

print("\n[Done]")

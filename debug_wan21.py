"""Discover actual API endpoints and test them."""
import os, sys, time, shutil
os.environ["OMP_NUM_THREADS"] = "1"

from gradio_client import Client

PROMPT = "a cute anime cat walking through a magical forest, colorful butterflies flying, children cartoon, high quality animation"

# 1. Check AnimateDiff-Lightning endpoints
print("="*60)
print("[1] ByteDance/AnimateDiff-Lightning")
print("="*60)
try:
    client = Client("ByteDance/AnimateDiff-Lightning")
    print(f"Endpoints: {client.view_api(print_info=False)}")
    # Try common API names
    for api in ["/predict", "/run", "/generate", "/infer", "/click_btn"]:
        try:
            print(f"\n  Trying {api}...")
            result = client.predict(prompt=PROMPT, api_name=api)
            print(f"  Result: {result}")
            if isinstance(result, str) and os.path.exists(result):
                print(f"  >>> GOT VIDEO: {os.path.getsize(result)} bytes")
                shutil.copy(result, "assets/test_animatediff.mp4")
                break
        except Exception as e:
            err = str(e)[:100]
            print(f"  {api} failed: {err}")
except Exception as e:
    print(f"  Space failed: {e}")

# 2. Check Wan2.1 actual available API names
print("\n" + "="*60)
print("[2] Wan-AI/Wan2.1 - listing all APIs")
print("="*60)
try:
    client = Client("Wan-AI/Wan2.1")
    api_info = client.view_api(print_info=True)
except Exception as e:
    print(f"  Failed: {e}")

# 3. Try tencent/HunyuanVideo
print("\n" + "="*60)
print("[3] tencent/HunyuanVideo")
print("="*60)
try:
    client = Client("tencent/HunyuanVideo")
    api_info = client.view_api(print_info=True)
    for api in ["/predict", "/run", "/generate", "/infer"]:
        try:
            result = client.predict(prompt=PROMPT, api_name=api)
            print(f"  {api} Result: {result}")
            break
        except Exception as e:
            err = str(e)[:100]
            print(f"  {api}: {err}")
except Exception as e:
    print(f"  Space failed: {str(e)[:200]}")

# 4. Try Pyramid-Flow
print("\n" + "="*60)
print("[4] multimodalart/pyramid-flow")
print("="*60)
try:
    client = Client("multimodalart/pyramid-flow")
    api_info = client.view_api(print_info=True)
except Exception as e:
    print(f"  Space failed: {str(e)[:200]}")

# 5. Try THUDM/CogVideoX
print("\n" + "="*60)
print("[5] THUDM/CogVideoX-5B-Space")
print("="*60)
try:
    client = Client("THUDM/CogVideoX-5B-Space")
    api_info = client.view_api(print_info=True)
except Exception as e:
    print(f"  Space failed: {str(e)[:200]}")

print("\n[Done]")

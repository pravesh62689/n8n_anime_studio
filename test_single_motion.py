"""Quick test: generate ONE motion video scene from Wan2.1 with proper wait time."""
import os, sys, asyncio, time

os.environ["OMP_NUM_THREADS"] = "1"
sys.path.insert(0, os.getcwd())

from studio_core import generate_anime_video

async def main():
    print("="*60)
    print("MOTION VIDEO TEST - Single Scene")
    print("="*60)
    
    prompt = "a cute anime cat character walking playfully through a colorful magical forest, butterflies flying around, the cat is moving and jumping, children cartoon style, vibrant colors, high quality 2D animation"
    filename = "test_motion_scene.mp4"
    
    start = time.time()
    result = await generate_anime_video(
        prompt=prompt,
        filename=filename,
        duration=8.0,
        is_hero=True,
        conditioning_image=None
    )
    elapsed = time.time() - start
    
    print(f"\n{'='*60}")
    print(f"RESULT: {result}")
    print(f"TIME: {elapsed:.1f}s")
    if os.path.exists(result):
        size = os.path.getsize(result)
        print(f"SIZE: {size} bytes ({size/1024/1024:.1f} MB)")
        
        # Check if it's a real motion video by looking at file size
        # A zoompan on a 10s clip is ~700KB-1MB
        # A real Wan2.1 generated video should be 3-15MB
        if size > 2_000_000:
            print(">>> LIKELY REAL MOTION VIDEO! (>2MB)")
        else:
            print(">>> Likely zoompan fallback (<2MB)")
    print("="*60)

asyncio.run(main())

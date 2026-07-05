"""Check API and run a quick test on linoyts/wan2-1-VACE-fast."""
import os, sys
from gradio_client import Client, handle_file

space_name = "rahul7star/wan2-1-fast"
print(f"Connecting to {space_name}...")
try:
    client = Client(space_name)
    print("Available API endpoints:")
    client.view_api(print_info=True)
    
    # Try generating a video
    print("\nAttempting to generate a video...")
    result = client.predict(
        input_image=handle_file("assets/test_last_frame.png"),
        prompt="the cute anime cat is jumping and playing, looking happy, dynamic animation, 2d motion",
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
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")

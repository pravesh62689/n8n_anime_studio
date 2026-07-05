"""Check the API of multimodalart/stable-video-diffusion."""
from gradio_client import Client

print("Connecting to multimodalart/stable-video-diffusion...")
try:
    client = Client("multimodalart/stable-video-diffusion")
    client.view_api(print_info=True)
except Exception as e:
    print(f"Error: {e}")

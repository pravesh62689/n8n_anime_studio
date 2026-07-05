"""Check the API of multimodalart/wan2-1-fast."""
import os, sys, time
from gradio_client import Client

print("Connecting to multimodalart/wan2-1-fast...")
try:
    client = Client("multimodalart/wan2-1-fast")
    client.view_api(print_info=True)
except Exception as e:
    print(f"Error: {e}")

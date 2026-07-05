"""Check the API of black-forest-labs/FLUX.1-schnell."""
from gradio_client import Client

print("Connecting to black-forest-labs/FLUX.1-schnell...")
try:
    client = Client("black-forest-labs/FLUX.1-schnell")
    client.view_api(print_info=True)
except Exception as e:
    print(f"Error: {e}")

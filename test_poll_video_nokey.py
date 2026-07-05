"""Test Pollinations video generation without a key."""
import httpx, os

url = "https://gen.pollinations.ai/prompt/a%20cute%20anime%20cat%20walking"
# Or let's see if we can do GET to gen.pollinations.ai/video
print("Testing GET https://gen.pollinations.ai/prompt/a%20cute%20anime%20cat%20walking?model=video")
try:
    with httpx.Client() as client:
        res = client.get("https://gen.pollinations.ai/prompt/a%20cute%20anime%20cat%20walking?model=video", timeout=30.0)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting GET https://gen.pollinations.ai/video/a%20cute%20anime%20cat")
try:
    with httpx.Client() as client:
        res = client.get("https://gen.pollinations.ai/video/a%20cute%20anime%20cat", timeout=30.0)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

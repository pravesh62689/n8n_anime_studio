"""Test Pollinations image generator."""
import httpx

url = "https://image.pollinations.ai/prompt/a%20cute%20anime%20cat?width=896&height=512&nologo=true"
print(f"Requesting: {url}")
try:
    with httpx.Client() as client:
        res = client.get(url, timeout=30.0)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print(f"Success! Content length: {len(res.content)}")
            with open("test_pollinations_image.png", "wb") as f:
                f.write(res.content)
        else:
            print(f"Failed with content: {res.text}")
except Exception as e:
    print(f"Error: {e}")

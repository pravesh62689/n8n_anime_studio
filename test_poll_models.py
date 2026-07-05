"""Test different models on Pollinations."""
import httpx

models = ["flux", "flux-anime", "flux-realism", "flux-4o", "turbo"]
for model in models:
    url = f"https://image.pollinations.ai/prompt/a%20cute%20anime%20cat?width=896&height=512&nologo=true&model={model}&seed=42"
    print(f"Testing model '{model}': {url}")
    try:
        with httpx.Client() as client:
            res = client.get(url, timeout=20.0)
            print(f"  Status: {res.status_code}")
            if res.status_code == 200:
                print(f"  Success for model {model}! Size: {len(res.content)}")
                with open(f"test_poll_{model}.png", "wb") as f:
                    f.write(res.content)
                break
    except Exception as e:
        print(f"  Error: {e}")

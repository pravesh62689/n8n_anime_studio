import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import asyncio
from sentence_transformers import SentenceTransformer

async def main():
    print("Loading model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Model loaded. Encoding...")
    emb = model.encode("An adventurous ninja cat discovering a hidden cyber city").tolist()
    print(f"Encoding successful! Size: {len(emb)}")

if __name__ == "__main__":
    asyncio.run(main())

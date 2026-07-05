import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import sqlite3
import sqlite_vec
from sentence_transformers import SentenceTransformer

def main():
    print("1. Loading SentenceTransformer first...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("2. Encoding text...")
    emb = model.encode("Test topic text").tolist()
    print(f"Encoding success: {len(emb)}")
    
    print("3. Loading sqlite-vec...")
    db = sqlite3.connect(":memory:")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    print("4. sqlite-vec loaded successfully!")

if __name__ == "__main__":
    main()

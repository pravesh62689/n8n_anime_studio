import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import json
from pathlib import Path
from studio_core import setup_rag_db, get_768d_embedding, vec_quantize_binary

def main():
    print("Connecting to DB...")
    db = setup_rag_db()
    print("Generating embedding...")
    float_emb = get_768d_embedding("An adventurous ninja cat discovering a hidden cyber city")
    print("Quantizing...")
    binary_emb = vec_quantize_binary(float_emb)
    print("Executing query...")
    rows = db.execute(
        """SELECT performance_data, vec_distance_hamming(embedding, vec_bit(?)) AS distance
           FROM vec_analytics_binary
           ORDER BY distance ASC LIMIT 3""",
        [binary_emb]
    ).fetchall()
    print(f"Query successful! Rows: {len(rows)}")

if __name__ == "__main__":
    main()

"""
db.py — sqlite-vec backed store for Anime Studio.

Does the two jobs the original `vec_analytics` table was designed for but
never had anything writing into it:

  1. Originality Guard — is a new topic/script too close to recent ones?
     (YouTube's monetization policy explicitly penalizes "mass-produced
     content using a similar template" — this is the mechanical check
     for that, not a substitute for actually varying the stories.)

  2. Scene retention scoring — after a video is live and analytics have
     settled, map YouTube's retention curve onto scene boundaries and
     store a score per scene, so future script generation can eventually
     see which *kinds* of beats held viewers.

DESIGN NOTE — float32 vectors, not bit-quantized:
The original design used 1-bit-quantized vectors (`bit[384]` +
vec_distance_hamming) to save RAM. That matters at large scale; it does
not matter here. A few thousand rows of 384-dim float32 vectors is a few
megabytes, against a 12GB machine. Plain float32 vec0 tables are simpler,
directly supported by sqlite-vec's standard MATCH/KNN query path (verified
empirically — the bit[] path requires pre-quantizing every vector through
vec_quantize_binary() and is a lot of extra fragility for a saving you
don't need at this data scale). If your dataset ever grows into the
millions of rows, revisit this — not before.

Run `python db.py --init` once to create the schema.
"""
import argparse
import datetime
import json
import os
import sqlite3
from pathlib import Path
from typing import Optional

import sqlite_vec

EMBED_DIM = 384  # all-MiniLM-L6-v2's output size

_model = None  # lazy singleton — loaded once, on one thread, on first use


def get_embedder():
    """Lazy-load sentence-transformers. Kept out of module import time so
    scripts that only need e.g. score_scene() don't pay the model-load cost."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed(text: str) -> bytes:
    """Returns a raw float32 blob sqlite-vec can store/query directly."""
    vec = get_embedder().encode(text, normalize_embeddings=True)
    return vec.astype("float32").tobytes()


def get_db(path: Optional[str] = None) -> sqlite3.Connection:
    path = path or os.environ.get("RAG_DB_PATH", "analytics_rag.db")
    db = sqlite3.connect(path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db


def init_db(path: Optional[str] = None) -> None:
    db = get_db(path)
    db.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_scripts USING vec0(
            embedding float[{EMBED_DIM}],
            +topic TEXT,
            +script_text TEXT,
            +created_at TEXT
        )
    """)
    db.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_analytics USING vec0(
            embedding float[{EMBED_DIM}],
            +video_id TEXT,
            +scene_id TEXT,
            +performance_data TEXT
        )
    """)
    db.commit()
    db.close()
    print(f"Initialized schema at {path or os.environ.get('RAG_DB_PATH', 'analytics_rag.db')}")


def _cosine_from_l2(l2_distance: float) -> float:
    """sqlite-vec returns L2 distance. For unit-normalized vectors,
    L2^2 = 2 - 2*cosine  =>  cosine = 1 - L2^2 / 2."""
    return 1 - (l2_distance ** 2) / 2


def check_originality(topic: str, script_text: str, db: sqlite3.Connection,
                       threshold: Optional[float] = None,
                       lookback: Optional[int] = None) -> dict:
    """
    Returns {"is_original": bool, "closest_score": float, "closest_topic": str|None}.
    closest_score is cosine similarity (0..1); higher = more similar.
    """
    threshold = threshold if threshold is not None else float(
        os.environ.get("ORIGINALITY_SIMILARITY_THRESHOLD", 0.87))
    lookback = lookback or int(os.environ.get("ORIGINALITY_LOOKBACK", 20))

    query_vec = embed(f"{topic}\n{script_text[:2000]}")
    rows = db.execute(
        """
        SELECT topic, distance FROM vec_scripts
        WHERE embedding MATCH ? AND k = ?
        ORDER BY distance
        """,
        [query_vec, lookback],
    ).fetchall()

    if not rows:
        return {"is_original": True, "closest_score": 0.0, "closest_topic": None}

    closest_topic, closest_l2 = rows[0]
    closest_cosine = _cosine_from_l2(closest_l2)
    return {
        "is_original": closest_cosine < threshold,
        "closest_score": closest_cosine,
        "closest_topic": closest_topic,
    }


def store_script(topic: str, script_text: str, db: sqlite3.Connection) -> None:
    db.execute(
        "INSERT INTO vec_scripts (embedding, topic, script_text, created_at) VALUES (?, ?, ?, ?)",
        [embed(f"{topic}\n{script_text[:2000]}"), topic, script_text,
         datetime.datetime.utcnow().isoformat()],
    )
    db.commit()


def store_scene_score(video_id: str, scene_id: str, scene_text: str,
                       score: dict, db: sqlite3.Connection) -> None:
    db.execute(
        "INSERT INTO vec_analytics (embedding, video_id, scene_id, performance_data) VALUES (?, ?, ?, ?)",
        [embed(scene_text), video_id, scene_id, json.dumps(score)],
    )
    db.commit()


def analytics_row_count(db: sqlite3.Connection) -> int:
    return db.execute("SELECT COUNT(*) FROM vec_analytics").fetchone()[0]


def query_similar_beats(scene_text: str, db: sqlite3.Connection, top_k: int = 5) -> list[dict]:
    """
    RAG retrieval, biased toward what actually held retention.

    Cold-start gate: with too few rows this returns noise dressed as
    signal. Callers should check analytics_row_count() against
    MIN_ANALYTICS_ROWS_FOR_RAG_BIAS before trusting this — see llm.py.
    """
    query_vec = embed(scene_text)
    rows = db.execute(
        """
        SELECT scene_id, performance_data, distance FROM vec_analytics
        WHERE embedding MATCH ? AND k = ?
        ORDER BY distance
        """,
        [query_vec, top_k],
    ).fetchall()
    results = []
    for scene_id, perf_json, distance in rows:
        perf = json.loads(perf_json)
        results.append({"scene_id": scene_id, "similarity": _cosine_from_l2(distance), **perf})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", action="store_true", help="Create the schema and exit")
    parser.add_argument("--db", default=None, help="Override RAG_DB_PATH")
    args = parser.parse_args()
    if args.init:
        init_db(args.db)
    else:
        parser.print_help()

import os
# Thread safety on Windows (MKL/OpenMP deadlock prevention)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import sys
import json
import subprocess
from pathlib import Path
from fastmcp import FastMCP
from dotenv import load_dotenv

# Light-weight imports (no PyTorch, sqlite-vec, edge-tts or pysubs2 loaded globally)
from studio_core import (
    generate_anime_video,
    synthesize_hindi_audio,
    render_scene_60fps,
)

load_dotenv()

MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")
MCP_HOST      = os.getenv("MCP_HOST",      "0.0.0.0")
MCP_PORT      = int(os.getenv("MCP_PORT",  "8000"))

# FastMCP Server
mcp = FastMCP("Anime_Studio_Server")

# -----------------------------------------------------------------------------
# TOOL 1: LLM Script Generator (Subprocess isolated)
# -----------------------------------------------------------------------------
@mcp.tool()
def generate_script(topic: str, duration: int = 4) -> list:
    """
    Generates a children's rhyme script in Hindi using Pollinations Text / OpenRouter cascade.
    Runs in isolated subprocess to prevent thread deadlocks.
    """
    script_output = Path.cwd() / "assets" / "mcp_temp_script.json"
    cmd = [
        ".venv\\Scripts\\python.exe", "studio_script_helper.py",
        "--action", "generate",
        "--topic", topic,
        "--duration", str(duration),
        "--output", str(script_output)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Script helper failed: {res.stderr}")
        
    with open(script_output, "r", encoding="utf-8") as f:
        script = json.load(f)
    if script_output.exists():
        script_output.unlink()
    return script

# -----------------------------------------------------------------------------
# TOOL 2: Visual Generator
# -----------------------------------------------------------------------------
@mcp.tool()
async def generate_visual(prompt: str, filename: str) -> str:
    """Generates an anime scene video or loop fallback from Pollinations."""
    return await generate_anime_video(prompt, filename)

# -----------------------------------------------------------------------------
# TOOL 3: Audio + Subtitle Generator
# -----------------------------------------------------------------------------
@mcp.tool()
async def synthesize_audio(text: str, base_filename: str, voice: str = "hi-IN-SwaraNeural") -> dict:
    """Generates SwaraNeural Hindi speech (or specified voice) and bottom center styled ASS subtitles."""
    return await synthesize_hindi_audio(text, base_filename, voice)

# -----------------------------------------------------------------------------
# TOOL 4: 60 FPS Compositor
# -----------------------------------------------------------------------------
@mcp.tool()
async def render_scene(
    video_path: str, audio_path: str, subtitle_path: str, base_filename: str
) -> dict:
    """Composites scene at 60 FPS using CPU H.264 sidechain compressed music bed."""
    return await render_scene_60fps(video_path, audio_path, subtitle_path, base_filename)

# -----------------------------------------------------------------------------
# TOOL 5: RAG Performance Ingest (Subprocess isolated)
# -----------------------------------------------------------------------------
@mcp.tool()
def ingest_performance_data(video_id: str, script_text: str, score: int) -> str:
    """Ingests video retention performance data into SQLite RAG database."""
    cmd = [
        ".venv\\Scripts\\python.exe", "studio_script_helper.py",
        "--action", "ingest",
        "--video-id", video_id,
        "--script-text", script_text,
        "--score", str(score)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Ingest helper failed: {res.stderr}")
    return f"Successfully ingested {video_id}."

if __name__ == "__main__":
    print(f"Starting MCP server on {MCP_HOST}:{MCP_PORT}")
    mcp.run(transport=MCP_TRANSPORT, host=MCP_HOST, port=MCP_PORT)

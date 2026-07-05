"""
content_mcp.py — Lightweight Content-Only MCP Server
======================================================
Exposes only the script generation and image download tools as a
minimal FastMCP server — useful as a lightweight sidecar alongside
the full studio_mcp.py, or standalone for content-only workflows.

Uses the same OpenRouter free-tier cascade as studio_core.py.
No Gemini SDK. No paid API. 100% free.
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import platform
platform.system = lambda: "Windows"
class _MockUname:
    system = "Windows"; node = "localhost"; release = "10"
    version = "10.0.0"; machine = "AMD64"; processor = "Intel"
    def __getitem__(self, idx):
        return [self.system, self.node, self.release,
                self.version, self.machine, self.processor][idx]
platform.uname = lambda: _MockUname()

import asyncio
import urllib.parse
import httpx
from pathlib import Path
from fastmcp import FastMCP
from dotenv import load_dotenv

# Import script generator from the core engine (no duplication)
from studio_core import generate_antigravity_script as _generate_script

load_dotenv()

mcp = FastMCP("Content_Server")

ASSETS_DIR = Path(os.getenv("STUDIO_ASSETS_DIR", "assets"))
POLLINATIONS_IMAGE = os.getenv(
    "POLLINATIONS_IMAGE_URL", "https://image.pollinations.ai/prompt/"
)


@mcp.tool()
def generate_script(topic: str) -> list:
    """
    Generates a 4-scene anime script using the OpenRouter free-tier cascade.
    Cascade: Llama 3.3 70B → Nemotron 3 Super 120B → Qwen3 Next 80B → offline fallback.
    Returns a list of dicts: [{"scene_prompt": str, "narration": str}, ...]
    """
    return _generate_script(topic)


@mcp.tool()
async def generate_anime_image(prompt: str, filename: str) -> str:
    """
    Downloads a high-resolution anime-style image from Pollinations.ai.
    Returns the absolute path to the saved PNG file.
    """
    anime_prompt = f"japanese anime style, 2d animation, high dynamic motion, {prompt}"
    encoded = urllib.parse.quote(anime_prompt)
    url = (
        f"{POLLINATIONS_IMAGE.rstrip('/')}/{encoded}"
        "?width=1920&height=1080&nologo=true&seed=42&enhance=true"
    )

    output_path = Path.cwd() / ASSETS_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=120.0)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)

    return str(output_path)


if __name__ == "__main__":
    port = int(os.getenv("CONTENT_MCP_PORT", "8001"))
    print(f"Content Server starting on http://0.0.0.0:{port}")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)

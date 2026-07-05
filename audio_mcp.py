import asyncio
from pathlib import Path
import edge_tts
import pysubs2
from fastmcp import FastMCP

mcp = FastMCP("Audio_Server")

@mcp.tool()
async def synthesize_audio_with_karaoke(text: str, voice: str, base_filename: str) -> dict:
    """
    Synthesizes neural voice and maps word boundaries into high-end karaoke styling.
    """
    assets_dir = Path.cwd() / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    audio_path = assets_dir / f"{base_filename}.mp3"
    srt_path = assets_dir / f"{base_filename}.srt"
    ass_path = assets_dir / f"{base_filename}.ass"
    
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    
    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
                
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        srt_file.write(submaker.get_srt())
        
    subs = pysubs2.load(str(srt_path), encoding="utf-8")
    for line in subs:
        # Custom bright yellow karaoke text overlay formatting with solid black border tracking
        line.text = "{\\1c&H00FFFF&}{\\3c&H000000&}{\\b1}{\\fs42}" + line.text
    subs.save(str(ass_path))
    
    return {
        "audio_file": str(audio_path),
        "subtitle_file": str(ass_path)
    }

if __name__ == "__main__":
    mcp.run()

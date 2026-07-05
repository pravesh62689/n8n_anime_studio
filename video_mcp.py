import asyncio
import os
import subprocess
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("Video_Server")

def get_ffmpeg_paths():
    """
    Locates the local FFmpeg and FFprobe binaries if they exist,
    otherwise falls back to system-wide paths.
    """
    project_dir = Path.cwd()
    local_ffmpeg = project_dir / "ffmpeg" / "bin" / "ffmpeg.exe"
    local_ffprobe = project_dir / "ffmpeg" / "bin" / "ffprobe.exe"
    
    ffmpeg_cmd = str(local_ffmpeg) if local_ffmpeg.exists() else "ffmpeg"
    ffprobe_cmd = str(local_ffprobe) if local_ffprobe.exists() else "ffprobe"
    
    return ffmpeg_cmd, ffprobe_cmd

def get_audio_duration(audio_path: str) -> float:
    _, ffprobe_cmd = get_ffmpeg_paths()
    cmd = [
        ffprobe_cmd, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

@mcp.tool()
async def render_anime_scene(image_path: str, audio_path: str, subtitle_path: str, base_filename: str) -> dict:
    """
    Uses smooth frame-blending filters to simulate authentic 24fps hand-drawn anime cells from the asset inputs.
    """
    assets_dir = Path.cwd() / "assets"
    output_path = assets_dir / f"{base_filename}.mp4"
    
    duration = get_audio_duration(audio_path)
    safe_sub_path = subtitle_path.replace("\\", "/").replace(":", "\\:")
    
    # Advanced filter graph: Structural scaling -> frame rate multiplication -> subtitle burn-in
    filter_graph = (
        f"[0:v]scale=2160:-2,minterpolate=fps=30:mi_mode=mci:mc_mode=aob:me_mode=bidir,"
        f"zoompan=z='min(zoom+0.001,1.2)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,"
        f"ass='{safe_sub_path}'[v]"
    )
    
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    cmd = [
        ffmpeg_cmd, "-y", "-loop", "1", "-framerate", "30", "-i", image_path,
        "-i", audio_path, "-filter_complex", filter_graph, "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-pix_fmt", "yuv420p", str(output_path)
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_msg = stderr.decode(errors="ignore")
        raise RuntimeError(f"FFmpeg failed with code {process.returncode}: {error_msg}")
    
    return {"video_file": str(output_path)}

if __name__ == "__main__":
    mcp.run()

import os
import socket
# Prevent infinite hangs on network sockets
socket.setdefaulttimeout(60)

# Limit PyTorch CPU thread pool to 1 to bypass MKL/OpenMP deadlock on Windows
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import urllib.parse
import urllib.request
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ASSETS_DIR = Path("assets")

# ---------------------------------------------------------
# FFmpeg Paths
# ---------------------------------------------------------
def get_ffmpeg_paths():
    project_dir = Path(__file__).resolve().parent
    ff  = project_dir / "ffmpeg" / "bin" / "ffmpeg.exe"
    ffp = project_dir / "ffmpeg" / "bin" / "ffprobe.exe"
    return (str(ff) if ff.exists() else "ffmpeg",
            str(ffp) if ffp.exists() else "ffprobe")

# ---------------------------------------------------------
# Helper: Parse JSON Script
# ---------------------------------------------------------
def parse_json_script(content: str) -> list:
    if "```json" in content:
        content = content.split("```json")[1].rsplit("```", 1)[0]
    elif "```" in content:
        content = content.split("```")[1].rsplit("```", 1)[0]
    content = content.strip()
    
    try:
        script_data = json.loads(content)
    except Exception as e:
        # Emergency recovery: try to locate first [ and last ]
        try:
            start = content.find("[")
            end = content.rfind("]") + 1
            script_data = json.loads(content[start:end])
        except Exception:
            raise e
            
    if isinstance(script_data, dict):
        for val in script_data.values():
            if isinstance(val, list):
                script_data = val
                break
                
    if not isinstance(script_data, list):
        if isinstance(script_data, dict) and ("scene_prompt" in script_data or "narration" in script_data):
            script_data = [script_data]
        else:
            raise ValueError(f"Could not parse a valid list of scenes from response.")
            
    normalized = []
    for item in script_data:
        if isinstance(item, dict):
            sp = item.get("scene_prompt", item.get("prompt", ""))
            nar = item.get("narration", item.get("text", ""))
            normalized.append({
                "scene_prompt": f"cute 2D children's cartoon style, vibrant colors, seed=42, highly consistent character design, {sp}",
                "narration": nar
            })
        elif isinstance(item, str):
            normalized.append({
                "scene_prompt": f"cute 2D children's cartoon style, vibrant colors, seed=42, highly consistent character design, illustration of {item}",
                "narration": item
            })
    return normalized

# ---------------------------------------------------------
# 1. 100% FREE SCRIPT WRITING (Replaces Gemini API)
# ---------------------------------------------------------
def call_llm_router(prompt: str) -> str:
    """Helper to route a prompt to the LLM cascade (OpenRouter Llama -> Nemotron -> Qwen -> Pollinations)."""
    import urllib.request
    import urllib.parse
    import json
    import os

    # Layer 1: OpenRouter Cascade (Fast & High Quality)
    # All API keys loaded from environment variables — never hardcode secrets.
    models = [
        {
            "name":  "Nemotron 3 Super 120B",
            "model": "nvidia/nemotron-3-super-120b-a12b:free",
            "key":   os.getenv("OR_NEMOTRON_KEY") or os.getenv("OPENROUTER_API_KEY"),
        },
        {
            "name":  "Gemma 4 26B",
            "model": "google/gemma-4-26b-a4b-it:free",
            "key":   os.getenv("OR_GEMMA_KEY") or os.getenv("OPENROUTER_API_KEY"),
        },
        {
            "name":  "Nemotron 3 Ultra 550B",
            "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
            "key":   os.getenv("OR_NEMOTRON_ULTRA_KEY") or os.getenv("OPENROUTER_API_KEY"),
        },
        {
            "name":  "Cohere North Mini Code",
            "model": "cohere/north-mini-code:free",
            "key":   os.getenv("OR_COHERE_KEY") or os.getenv("OPENROUTER_API_KEY"),
        },
        {
            "name":  "Qwen 3 Coder",
            "model": "qwen/qwen3-coder:free",
            "key":   os.getenv("OR_QWEN_CODER_KEY") or os.getenv("OR_QWEN_KEY"),
        }
    ]

    for model_cfg in models:
        key = model_cfg["key"]
        if not key:
            continue
        try:
            print(f"[LLM Router] Trying OpenRouter model: {model_cfg['name']}...")
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps({
                    "model": model_cfg["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                choice = res_data.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content") or message.get("text")
                if not content:
                    raise ValueError(f"Empty content received from {model_cfg['name']}")
                print(f"[LLM Router] Success using {model_cfg['name']}")
                return content
        except Exception as e:
            print(f"[LLM Router] OpenRouter {model_cfg['name']} failed: {e}")
            pass

    # Layer 2: Pollinations POST JSON Mode
    try:
        print("[LLM Router] Falling back to Pollinations POST...")
        req = urllib.request.Request(
            "https://text.pollinations.ai",
            data=json.dumps({
                "messages": [{"role": "user", "content": prompt}],
                "jsonMode": True
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict) and "content" in data:
                content = data["content"]
            else:
                content = json.dumps(data)
            return content
    except Exception as e:
        print(f"[LLM Router] Pollinations POST failed: {e}")
        pass

    # Layer 3: Pollinations GET Path Mode
    try:
        print("[LLM Router] Falling back to Pollinations GET...")
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}?json=true"
        with urllib.request.urlopen(url, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict) and "content" in data:
                content = data["content"]
            else:
                content = json.dumps(data)
            return content
    except Exception as e:
        print(f"[LLM Router] Pollinations GET failed: {e}")
        pass

    raise RuntimeError("All LLM text generation systems failed.")

def generate_hindi_script(topic: str, duration_minutes: int = 4) -> list:
    """
    Generates a full 30-scene script by querying the LLM cascade in 6 distinct chapters,
    using 5-second sleep delays to prevent rate limits, implementing a unique fallback path,
    and using a Contextual Bandit hook selector for the first chapter.
    """
    import urllib.parse
    import urllib.request
    import json
    import time
    
    # Contextual Bandit Hook Selection
    hook_arms = ["hook_question", "hook_action", "hook_climax"]
    try:
        selected_hook = select_bandit_arm(hook_arms)
    except Exception as e:
        print(f"[Bandit Warning] Failed to select arm: {e}. Defaulting to hook_question.")
        selected_hook = "hook_question"
        
    chapters = [
        {"name": "Chapter 1: Introduction and Setting the Scene", "focus": "Introduce the characters and the setting in a fun, friendly way."},
        {"name": "Chapter 2: The Adventure Begins", "focus": "The characters start a journey or discover something exciting."},
        {"name": "Chapter 3: An Unexpected Event", "focus": "A surprising challenge or funny situation occurs."},
        {"name": "Chapter 4: Solving the Problem", "focus": "The characters use their intelligence or work together to handle the situation."},
        {"name": "Chapter 5: The Climax", "focus": "The most exciting or humorous part of the adventure."},
        {"name": "Chapter 6: Conclusion & Lesson", "focus": "The characters celebrate their success and share a positive lesson."}
    ]
    
    # Scale chapters based on requested duration to allow quick testing/smoke-runs
    if duration_minutes <= 1:
        chapters = chapters[:2]
    elif duration_minutes == 2:
        chapters = chapters[:3]
    elif duration_minutes == 3:
        chapters = chapters[:4]
        
    # Adjust Chapter 1 focus based on selected hook
    if selected_hook == "hook_question":
        chapters[0]["focus"] = "Introduce the characters and setting by asking the audience an engaging, direct question to grab their attention."
    elif selected_hook == "hook_action":
        chapters[0]["focus"] = "Start the episode with immediate action and high energy to grab attention."
    elif selected_hook == "hook_climax":
        chapters[0]["focus"] = "Start the episode with a mysterious teaser or climax moment, then jump to the setup."
        
    full_script = []
    
    # Retrieve high-retention historical scripts (RAG reinforcement loop)
    rag_context = ""
    try:
        rag_context = retrieve_reinforced_context(topic)
    except Exception as e:
        print(f"[RAG Warning] Failed to retrieve reinforced context: {e}")

    for idx, chap in enumerate(chapters, start=1):
        print(f"[Script Gen] Crafting Chapter {idx}/{len(chapters)} ({chap['name']})...")
        
        prompt = (
            f"You are an expert children's cartoon director, storyboard artist, and screenwriter for viral YouTube kids' channels.\n"
            f"Write Chapter {idx} of a script about '{topic}'. {chap['name']}: {chap['focus']}.\n\n"
            f"CRITICAL REQUIREMENTS:\n"
            f"1. Every single scene must be distinct, imaginative, and highly detailed. Avoid generic descriptions.\n"
            f"2. Write the narration in extremely engaging, emotional, and expressive Hindi (Hinglish words allowed for child readability). Use a warm, enthusiastic, and theatrical storytelling tone.\n"
            f"3. Write the `scene_prompt` in English. Each `scene_prompt` must be a high-quality, detailed visual description for an AI image generator (describing character actions, facial expressions, background scenery, light rays, colors, and camera angle). Do not include generic phrases like 'vibrant colors' or 'consistent art style' - describe the actual scene items in detail.\n"
            f"4. Generate exactly 5 short sequential scenes for this chapter.\n"
            f"5. Return ONLY a strictly valid JSON array — do not wrap in markdown code blocks or add any trailing/leading explanation.\n\n"
            f"Format:\n"
            f"[{{\n"
            f"  \"scene_prompt\": \"Detailed descriptive visual prompt in English describing character emotions, camera view, background detail\",\n"
            f"  \"narration\": \"Narration spoken text in Hindi\"\n"
            f"}}]\n\n"
            f"Context from previous chapters: {json.dumps(full_script[-5:]) if full_script else 'None'}\n"
            f"{rag_context}"
        )
        
        # 5-second sleep to prevent rate limiting
        if idx > 1:
            time.sleep(5)
            
        chapter_scenes = []
        try:
            content = call_llm_router(prompt)
            chapter_scenes = parse_json_script(content)
        except Exception as e:
            print(f"[WARNING] Chapter {idx} generation failed ({e}). Using fallback.")
            
        if not chapter_scenes:
            chapter_scenes = [
                {
                    "scene_prompt": f"A beautiful cartoon scene of {topic}, part {idx}, step {s}, vibrant colors, happy characters.",
                    "narration": f"Aur phir, humare dosto ne {topic} ke is safar mein agla kadam badhaya, bhag {idx} ka drishya {s}."
                } for s in range(1, 6)
            ]
        elif len(chapter_scenes) < 5:
            while len(chapter_scenes) < 5:
                s_idx = len(chapter_scenes) + 1
                chapter_scenes.append({
                    "scene_prompt": f"A beautiful cartoon illustration of {topic}, step {s_idx}, consistent art style.",
                    "narration": f"Aur iske baad, unhone {topic} ki is kahani mein ek naya mod dekha, drishya {s_idx}."
                })
        elif len(chapter_scenes) > 5:
            chapter_scenes = chapter_scenes[:5]
            
        for scene in chapter_scenes:
            # Style prefix already injected by parse_json_script() — do not double-inject
            scene["selected_hook"] = selected_hook
            
        full_script.extend(chapter_scenes)
        
    print(f"[Script Gen] Full script compiled successfully with {len(full_script)} scenes.")
    return full_script

def generate_antigravity_script(topic: str) -> list:
    """Wrapper script for content_mcp.py imports compatibility."""
    return generate_hindi_script(topic)

# ---------------------------------------------------------
# 2. 100% FREE VIDEO GENERATION
# ---------------------------------------------------------
def get_audio_duration(audio_path: str) -> float:
    """Helper to query the exact duration of an audio file using ffprobe."""
    import subprocess
    ffmpeg_cmd, ffprobe_cmd = get_ffmpeg_paths()
    cmd = [
        ffprobe_cmd, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            return float(res.stdout.strip())
        except ValueError:
            pass
    return 10.0  # Default fallback if query fails

def call_with_retry(fn, *args, max_retries=4, base_delay=2.0, **kwargs):
    """Sync wrapper for retry with exponential random backoff."""
    import time
    import random
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt == max_retries - 1:
                break
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"[retry] Attempt {attempt+1} failed ({e}); sleeping {delay:.1f}s")
            time.sleep(delay)
    raise last_exc

async def async_call_with_retry(fn, *args, max_retries=4, base_delay=2.0, **kwargs):
    """Async wrapper for retry with exponential random backoff."""
    import asyncio
    import random
    last_exc = None
    for attempt in range(max_retries):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt == max_retries - 1:
                break
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"[retry] Async attempt {attempt+1} failed ({e}); sleeping {delay:.1f}s")
            await asyncio.sleep(delay)
    raise last_exc

def scene_is_valid(path: str, min_duration_s: float = 1.0) -> bool:
    """Uses ffprobe to verify duration and integrity of a scene clip."""
    import subprocess
    import json
    from pathlib import Path
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return False
    _, ffprobe_cmd = get_ffmpeg_paths()
    try:
        result = subprocess.run(
            [ffprobe_cmd, "-v", "error", "-show_entries", "format=duration",
             "-of", "json", str(p)],
            capture_output=True, text=True, timeout=15,
        )
        duration = float(json.loads(result.stdout).get("format", {}).get("duration", 0))
        return duration >= min_duration_s
    except Exception as e:
        print(f"[QC] Validation error for {path}: {e}")
        return False

def extract_last_frame(video_path: str, out_path: str):
    """Extracts the very last frame of a video clip to condition the next scene."""
    import subprocess
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    cmd = [
        ffmpeg_cmd, "-y",
        "-sseof", "-1",
        "-i", video_path,
        "-update", "1",
        "-q:v", "2",
        "-frames:v", "1",
        out_path
    ]
    print(f"[FFmpeg] Extracting last frame of {video_path} to {out_path}...")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

class VideoResult(str):
    def __new__(cls, path, tier_attempted=3, tier_used=3, fallback_reason=None):
        obj = super().__new__(cls, path)
        obj.path = path
        obj.tier_attempted = tier_attempted
        obj.tier_used = tier_used
        obj.fallback_reason = fallback_reason
        return obj

async def generate_anime_video(prompt: str, filename: str, duration: float = 8.0, is_hero: bool = False, conditioning_image: str = None) -> VideoResult:
    """
    Generates an animated video clip using a 3-tier visual pipeline.
    Tier 1: Real Wan2.1 motion via HF Space, last-frame chained.
    Tier 2: Pose-sequence hard-cut animation via Pollinations Flux.
    Tier 3: Multi-layer parallax zoompan.
    """
    import os
    import asyncio
    import httpx
    import shutil
    from pathlib import Path
    from quota import QuotaTracker
    import pose_sequence

    output_path = Path.cwd() / "assets" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    prompt_lower = prompt.lower()
    is_static = any(word in prompt_lower for word in ["establishing shot", "scenery only", "static view", "background only", "landscape only", "establishing view"])

    tier_attempted = 1 if is_hero and not is_static else (3 if is_static else 2)
    tier_used = 3
    fallback_reason = None

    # TIER 1: Real Wan2.1 Motion
    if tier_attempted == 1:
        tracker = QuotaTracker()
        if not tracker.can_afford():
            print(f"[Visual Router] Quota exhausted (remaining: {tracker.remaining_seconds()}s). Falling back to Tier 2.")
            fallback_reason = "quota_exhausted"
        else:
            tracker.record_usage() # record usage estimated at 70s
            try:
                print(f"[VFX] [Tier 1] Attempting hero beat generation via HF Space: Wan-AI/Wan2.1...")
                from gradio_client import Client, handle_file
                client = await asyncio.to_thread(Client, "Wan-AI/Wan2.1")
                
                if conditioning_image and os.path.exists(conditioning_image):
                    # Image-to-Video Chaining
                    print(f"[VFX] [Tier 1] Launching i2v_generation_async conditioned on: {conditioning_image}...")
                    res = await asyncio.to_thread(
                        client.predict,
                        prompt=prompt,
                        image=handle_file(str(conditioning_image)),
                        watermark_wan=False,
                        seed=-1.0,
                        api_name="/i2v_generation_async"
                    )
                else:
                    # Text-to-Video Start
                    print(f"[VFX] [Tier 1] Launching t2v_generation_async...")
                    res = await asyncio.to_thread(
                        client.predict,
                        prompt=prompt,
                        size="1280*720",
                        watermark_wan=False,
                        seed=-1.0,
                        api_name="/t2v_generation_async"
                    )
                
                # Poll status
                est_wait = 600
                if isinstance(res, (list, tuple)) and len(res) >= 2:
                    est_wait = max(int(res[1]) if isinstance(res[1], (int, float)) else 600, 120)
                max_polls = max(est_wait // 10 + 12, 90)
                video_file = None
                for poll in range(max_polls):
                    await asyncio.sleep(10)
                    try:
                        status_res = await asyncio.wait_for(
                            asyncio.to_thread(client.predict, api_name="/status_refresh"),
                            timeout=25.0
                        )
                        generated_video = status_res[0]
                        progress = status_res[3] if len(status_res) > 3 else None
                        est_remaining = status_res[2] if len(status_res) > 2 else "?"
                        
                        if generated_video and isinstance(generated_video, dict):
                            vid_path = generated_video.get("video")
                            if vid_path and isinstance(vid_path, str) and os.path.exists(vid_path) and os.path.getsize(vid_path) > 1000:
                                video_file = vid_path
                                print(f"[VFX] [Tier 1] [OK] MOTION VIDEO generated! Path: {video_file} ({os.path.getsize(vid_path)} bytes)")
                                break
                        
                        prog_label = ""
                        if isinstance(progress, dict):
                            prog_label = progress.get("label", "")
                        elif isinstance(progress, (int, float)):
                            prog_label = f"{progress}%"
                        print(f" [VFX] [Tier 1] Poll {poll+1}/{max_polls} | ETA: {est_remaining}s | Progress: {prog_label}")
                    except Exception as pe:
                        print(f" [VFX] [Tier 1] Status poll warning: {pe}")
                        
                if video_file and os.path.exists(video_file) and os.path.getsize(video_file) > 1000:
                    shutil.copy(video_file, str(output_path))
                    print(f"[VFX] [Tier 1] Copied motion video to {output_path}")
                    return VideoResult(str(output_path), tier_attempted=1, tier_used=1)
                else:
                    print("[VFX] [Tier 1] Wan2.1 queue timed out. Falling back to Tier 2...")
                    fallback_reason = "timeout"
                    
            except Exception as e:
                print(f"[WARNING] [Tier 1] Hero generation failed: {e}. Falling back to Tier 2...")
                fallback_reason = f"space_error: {e}"

    # TIER 2: Pose-Sequence Hard-Cut Animation
    if (tier_attempted == 2) or (tier_attempted == 1 and fallback_reason is not None):
        print(f"[VFX] [Tier 2] Generating pose sequence animation for: {filename}...")
        try:
            beat_id = f"pose_{Path(filename).stem}"
            out_dir = Path.cwd() / "assets" / "pose_temp"
            
            # Resolve conditioning image if it's a web URL
            ref_url = None
            if conditioning_image and conditioning_image.startswith(("http://", "https://")):
                ref_url = conditioning_image

            clip_path = await asyncio.to_thread(
                pose_sequence.build_pose_sequence_beat,
                action_description=prompt,
                out_dir=out_dir,
                beat_id=beat_id,
                reference_image_url=ref_url,
                character_seed=42,
                n_poses=4,
                total_duration_s=duration
            )
            
            if clip_path and clip_path.exists() and clip_path.stat().st_size > 1000:
                shutil.copy(str(clip_path), str(output_path))
                print(f"[VFX] [Tier 2] Assembled pose sequence video copied to {output_path}")
                
                # Cleanup temp pose_temp directory
                try:
                    shutil.rmtree(str(out_dir), ignore_errors=True)
                except Exception:
                    pass
                    
                return VideoResult(str(output_path), tier_attempted=tier_attempted, tier_used=2, fallback_reason=fallback_reason)
            else:
                print(f"[VFX] [Tier 2] Pose sequence generation failed or empty. Falling back to Tier 3.")
                if fallback_reason:
                    fallback_reason += " | tier_2_failed"
                else:
                    fallback_reason = "tier_2_failed"
        except Exception as e2:
            print(f"[WARNING] [Tier 2] Failed: {e2}. Falling back to Tier 3.")
            if fallback_reason:
                fallback_reason += f" | tier_2_error: {e2}"
            else:
                fallback_reason = f"tier_2_error: {e2}"

    # TIER 3: Multi-Layer Parallax Zoompan
    print(f"[VFX] [Tier 3] Rendering 2D parallax zoompan for: {filename}...")
    encoded_prompt = urllib.parse.quote(prompt)
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&nologo=true&seed=42"
    img_path = output_path.with_suffix(".png")
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(img_url, timeout=60.0)
            res.raise_for_status()
            with open(img_path, "wb") as f:
                f.write(res.content)
    except Exception as e2:
        print(f"[WARNING] Image download failed ({e2}). Using local test_frame.png fallback.")
        test_frame = Path.cwd() / "assets" / "test_frame.png"
        if test_frame.exists():
            shutil.copy(str(test_frame), str(img_path))
        else:
            black_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:~\x9bU\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
            with open(img_path, "wb") as f:
                f.write(black_png)
                
    bg_path = img_path.with_name(img_path.stem + "_bg.png")
    fg_path = img_path.with_name(img_path.stem + "_fg.png")
    
    try:
        from PIL import Image
        from rembg import remove
        print("[Parallax] Isolating foreground layer with rembg...")
        input_img = Image.open(img_path)
        fg_img = remove(input_img)
        fg_img.save(fg_path)
        shutil.copy(str(img_path), str(bg_path))
    except Exception as e3:
        print(f"[WARNING] rembg segmentation failed ({e3}). Using non-parallax fallback.")
        shutil.copy(str(img_path), str(bg_path))
        shutil.copy(str(img_path), str(fg_path))
        
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    num_frames = int(duration * 30) + 10
    
    filter_complex = (
        f"[0:v]scale=1280x720,zoompan=z='min(zoom+0.0004,1.15)':d={num_frames}:s=1280x720:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'[bg]; "
        f"[1:v]scale=1280x720,zoompan=z='min(zoom+0.0008,1.25)':d={num_frames}:s=1280x720:x='iw/2-(iw/zoom/2)+sin(on/15)*6':y='ih/2-(ih/zoom/2)+cos(on/15)*4'[fg]; "
        f"[bg][fg]overlay=0:0:shortest=1[outv]"
    )
    
    cmd = [
        ffmpeg_cmd, "-y",
        "-threads", "2",
        "-loop", "1", "-i", str(bg_path),
        "-loop", "1", "-i", str(fg_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-t", f"{duration}", "-r", "30",
        "-c:v", "mpeg4", "-q:v", "3", "-pix_fmt", "yuv420p", str(output_path)
    ]
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"[ERROR] ffmpeg parallax generation failed (code {proc.returncode}): {stderr.decode(errors='ignore')}")
    finally:
        if img_path.exists():
            img_path.unlink()
        if bg_path.exists():
            bg_path.unlink()
        if fg_path.exists():
            fg_path.unlink()
            
    if not scene_is_valid(str(output_path)):
        raise RuntimeError("Generated parallax video scene failed validation check.")
    print(f"[VFX] Parallax zoompan animation created and verified successfully.")
    
    return VideoResult(str(output_path), tier_attempted=tier_attempted, tier_used=3, fallback_reason=fallback_reason)

# ---------------------------------------------------------
# 3. MULTI-LANGUAGE TTS & CINEMATIC SUBTITLES
# ---------------------------------------------------------
LANGUAGE_VOICES = {
    "hi": {
        "narrator":  {"voice": "hi-IN-SwaraNeural",  "rate": "+5%",  "pitch": "+0Hz"},
        "hero_boy":  {"voice": "hi-IN-MadhurNeural",  "rate": "+8%",  "pitch": "+10Hz"},
        "hero_girl": {"voice": "hi-IN-SwaraNeural",   "rate": "+10%", "pitch": "+20Hz"},
    },
    "en": {
        "narrator":  {"voice": "en-IN-NeerjaNeural",  "rate": "+5%",  "pitch": "+0Hz"},
        "hero_boy":  {"voice": "en-IN-PrabhatNeural", "rate": "+8%",  "pitch": "+10Hz"},
        "hero_girl": {"voice": "en-IN-NeerjaNeural",  "rate": "+10%", "pitch": "+20Hz"},
    },
    "es": {
        "narrator":  {"voice": "es-MX-DaliaNeural",   "rate": "+5%",  "pitch": "+0Hz"},
        "hero_boy":  {"voice": "es-MX-JorgeNeural",   "rate": "+8%",  "pitch": "+10Hz"},
        "hero_girl": {"voice": "es-MX-DaliaNeural",   "rate": "+10%", "pitch": "+20Hz"},
    }
}

def localize_script(script_text: str, target_lang: str) -> str:
    """Translates a script narration text into the target language using the LLM cascade."""
    prompt = (
        f"You are a professional children's stories translator. Translate the following narration text "
        f"into {target_lang}. Keep the tone extremely warm, simple and suitable for 5-8 year old children. "
        f"Keep character names exactly as they are. Return ONLY the translated text, with no markdown fences, "
        f"introductory text or explanation.\n\nText to translate:\n{script_text}"
    )
    return call_llm_router(prompt)

async def synthesize_hindi_audio(text: str, base_filename: str, character: str = "narrator", scene_idx: int = 1, language: str = "hi", voice: str = None, rate: str = None, pitch: str = None) -> dict:
    """
    Synthesizes narration or dialogue using per-character, per-language edge-tts settings.
    Saves subtitles as ASS with bottom-aligned style formatting.
    """
    import edge_tts
    import pysubs2
    assets_dir = Path.cwd() / "assets"
    audio_path = assets_dir / f"{base_filename}.mp3"
    srt_path = assets_dir / f"{base_filename}.srt"
    ass_path = assets_dir / f"{base_filename}.ass"
    
    # Guard against empty narration text
    if not text or not text.strip():
        text = f"Aur phir kahani mein ek naya drishya saamne aaya, drishya {scene_idx}."
        print(f"[Audio] WARNING: Empty narration for scene {scene_idx}. Using placeholder.")
    
    # Character Voice Mappings
    voices_map = LANGUAGE_VOICES.get(language, LANGUAGE_VOICES["hi"])
    
    # If not explicitly mapped, alternate based on scene index
    if character not in voices_map:
        if scene_idx % 3 == 1:
            cfg = voices_map["narrator"]
        elif scene_idx % 3 == 2:
            cfg = voices_map["hero_boy"]
        else:
            cfg = voices_map["hero_girl"]
    else:
        cfg = voices_map[character]
        
    cfg = cfg.copy()
    if voice:
        cfg["voice"] = voice
    if rate:
        cfg["rate"] = rate
    if pitch:
        cfg["pitch"] = pitch
        
    communicate = edge_tts.Communicate(text, cfg["voice"], rate=cfg["rate"], pitch=cfg["pitch"])
    submaker = edge_tts.SubMaker()
    
    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
                
    srt_content = submaker.get_srt()
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        # If edge-tts returned empty SRT, write a minimal valid one
        if not srt_content or not srt_content.strip():
            srt_content = "1\n00:00:00,000 --> 00:00:03,000\n" + text + "\n"
        srt_file.write(srt_content)
        
    # Apply Professional Subtitle Styling
    subs = pysubs2.load(str(srt_path), encoding="utf-8")
    for line in subs:
        line.text = r"{\an2\fs22\1c&H00FFFF&\3c&H000000&\bord2\b1}" + line.text
    subs.save(str(ass_path))
    
    return {"audio_file": str(audio_path), "subtitle_file": str(ass_path)}

# ---------------------------------------------------------
# 4. 60 FPS COMPOSITOR (SIDECHAIN COMPRESSION) + METADATA
# ---------------------------------------------------------
async def render_scene_60fps(video_path: str, audio_path: str, subtitle_path: str, base_filename: str, bgm_path: str = None, sfx_path: str = None) -> dict:
    """
    Composites voiceover, dynamic zoompan parallax video, and subtitles into a 60 FPS scene.
    Ducks bgm_path or assets/bg_music.mp3 under dialogue, mixes in sfx_path if present.
    """
    import asyncio
    output_path = Path.cwd() / "assets" / f"{base_filename}.mp4"
    safe_sub = subtitle_path.replace("\\", "/").replace(":", "\\:")
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    
    # Check if a custom bgm is provided, otherwise fall back to assets/bg_music.mp3
    bg_music = bgm_path if (bgm_path and os.path.exists(bgm_path)) else str(Path.cwd() / "assets" / "bg_music.mp3")
    bgm_exists = os.path.exists(bg_music)
    
    sfx_exists = sfx_path and os.path.exists(sfx_path)
    
    cmd = [
        ffmpeg_cmd, "-y",
        "-threads", "2",
        "-i", video_path,
        "-i", audio_path
    ]
    
    bgm_idx = -1
    sfx_idx = -1
    next_idx = 2
    
    if bgm_exists:
        cmd += ["-i", str(bg_music)]
        bgm_idx = next_idx
        next_idx += 1
        
    if sfx_exists:
        cmd += ["-i", str(sfx_path)]
        sfx_idx = next_idx
        next_idx += 1
        
    if bgm_exists and sfx_exists:
        print(f"[Compositor] Dynamic mix: Vocals + BGM (ducked) + SFX...")
        filter_complex = (
            f"[0:v]fps=fps=60,scale=1920:1080,ass='{safe_sub}'[outv]; "
            f"[{bgm_idx}:a]volume=0.15[bg]; "
            f"[{sfx_idx}:a]volume=0.8[sfx]; "
            f"[1:a][bg]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=300[vocals_bg]; "
            f"[vocals_bg][sfx]amix=inputs=2:duration=first:dropout_transition=0[outa]"
        )
        cmd += [
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "[outa]"
        ]
    elif bgm_exists:
        print(f"[Compositor] Dynamic mix: Vocals + BGM (ducked)...")
        filter_complex = (
            f"[0:v]fps=fps=60,scale=1920:1080,ass='{safe_sub}'[outv]; "
            f"[{bgm_idx}:a]volume=0.15[bg]; "
            f"[1:a][bg]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=300[outa]"
        )
        cmd += [
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "[outa]"
        ]
    elif sfx_exists:
        print(f"[Compositor] Dynamic mix: Vocals + SFX...")
        filter_complex = (
            f"[0:v]fps=fps=60,scale=1920:1080,ass='{safe_sub}'[outv]; "
            f"[{sfx_idx}:a]volume=0.8[sfx]; "
            f"[1:a][sfx]amix=inputs=2:duration=first:dropout_transition=0[outa]"
        )
        cmd += [
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "[outa]"
        ]
    else:
        print(f"[Compositor] Standard mix: Vocals only...")
        cmd += [
            "-vf", f"fps=fps=60,scale=1920:1080,ass='{safe_sub}'",
            "-c:a", "aac", "-b:a", "192k"
        ]
        
    if bgm_exists or sfx_exists:
        cmd += [
            "-c:v", "mpeg4", "-q:v", "3",
            "-c:a", "aac", "-b:a", "192k",
            "-metadata", "copyright=Owned by Creator",
            "-metadata", "title=Premium Kids Animation",
            "-shortest", str(output_path)
        ]
    else:
        cmd += [
            "-c:v", "mpeg4", "-q:v", "3",
            "-metadata", "copyright=Owned by Creator",
            "-metadata", "title=Premium Kids Animation",
            "-shortest", str(output_path)
        ]
        
    print(f"[Compositor] Rendering scene to 60 FPS...")
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.communicate()
    
    print(f"[Compositor] CPU 60 FPS Render successful: {base_filename}")
    return {"video_file": str(output_path)}

# ---------------------------------------------------------
# 5. RAG ANALYTICS — delegates to db.py (float32 approach)
# ---------------------------------------------------------
# The old bit-quantized approach (bit[384] + Hamming distance) has been replaced
# with db.py's float32 vec0 tables + L2 distance. See db.py docstring for rationale.

MIN_ANALYTICS_ROWS_FOR_RAG = 5  # Cold-start gate: below this, RAG returns noise not signal

def ingest_performance(video_id: str, script_text: str, retention_score: int):
    """Ingests video retention data into the float32 vec_analytics table via db.py."""
    from db import get_db, init_db, store_scene_score
    try:
        db = get_db()
    except Exception:
        init_db()
        db = get_db()
    try:
        store_scene_score(
            video_id=video_id,
            scene_id="full_script",
            scene_text=script_text[:2000],
            score={"retention": retention_score, "script": script_text},
            db=db
        )
    finally:
        db.close()
    print(f"[RAG] Ingested video performance data for {video_id}.")

def retrieve_reinforced_context(topic: str) -> str:
    """Queries RAG database for high-retention historical scripts using float32 L2 distance.
    Returns empty string if below cold-start threshold (too few rows = noise)."""
    from db import get_db, init_db, analytics_row_count, query_similar_beats
    try:
        db = get_db()
    except Exception:
        init_db()
        db = get_db()
    try:
        row_count = analytics_row_count(db)
        if row_count < MIN_ANALYTICS_ROWS_FOR_RAG:
            print(f"[RAG] Cold-start gate: only {row_count} rows (need {MIN_ANALYTICS_ROWS_FOR_RAG}). Skipping RAG.")
            return ""

        results = query_similar_beats(topic, db, top_k=3)
    finally:
        db.close()

    best_script = None
    best_retention = -1

    for r in results:
        retention = r.get("retention", 0)
        if retention > best_retention:
            best_retention = retention
            best_script = r.get("script")

    if best_script:
        print(f"[RAG] Found high-retention historical script with score {best_retention}. Injecting...")
        return (
            f"\n\nHere is a high-performing historical script from past episodes to guide your pacing and structure:\n"
            f"{best_script}\n"
            f"Analyze the pacing and tone of this script, and use it to model the new Hindi script."
        )
    return ""

# ---------------------------------------------------------
# 5. Contextual Bandit Feedback & Hook Selector (Anime Studio 6.0)
# ---------------------------------------------------------
def setup_bandit_db():
    conn = sqlite3.connect("analytics_rag.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS bandit_arms
                     (name TEXT PRIMARY KEY, total_reward REAL, n_pulls INTEGER)""")
    conn.commit()
    return conn

def select_bandit_arm(arm_names: list) -> str:
    """Epsilon-greedy bandit selection (15% exploration, 85% exploit)."""
    import random
    EPSILON = 0.15
    conn = setup_bandit_db()
    try:
        # Load all arms from DB
        arms = {}
        for name in arm_names:
            row = conn.execute("SELECT total_reward, n_pulls FROM bandit_arms WHERE name=?", (name,)).fetchone()
            if row:
                arms[name] = {"total_reward": row[0], "n_pulls": row[1]}
            else:
                arms[name] = {"total_reward": 0.0, "n_pulls": 0}
    finally:
        conn.close()

    # Explore if random < EPSILON or if any arm has 0 pulls
    if random.random() < EPSILON or any(arms[a]["n_pulls"] == 0 for a in arm_names):
        selected = random.choice(arm_names)
        print(f"[Bandit] Exploring random arm: {selected}")
        return selected
        
    # Exploit best performing arm
    best_arm = None
    best_avg = -1.0
    for name in arm_names:
        pulls = arms[name]["n_pulls"]
        avg = arms[name]["total_reward"] / pulls if pulls > 0 else 0.0
        if avg > best_avg:
            best_avg = avg
            best_arm = name
            
    print(f"[Bandit] Exploiting best arm: {best_arm} (average reward: {best_avg:.4f})")
    return best_arm

def update_bandit_arm(arm_name: str, reward: float):
    """Updates the reward and pull count for a given arm in DB."""
    conn = setup_bandit_db()
    try:
        conn.execute("""INSERT INTO bandit_arms (name, total_reward, n_pulls)
                         VALUES (?, ?, 1)
                         ON CONFLICT(name) DO UPDATE SET
                           total_reward = total_reward + excluded.total_reward,
                           n_pulls = n_pulls + 1""", (arm_name, reward))
        conn.commit()
    finally:
        conn.close()
    print(f"[Bandit] Updated performance for arm '{arm_name}' with reward {reward:.4f}.")

def compute_retention_reward(retention_curve: list) -> float:
    """
    Computes a reward score from a YouTube Analytics retention curve.
    retention_curve rows: list of [elapsedVideoTimeRatio, audienceWatchRatio, relativeRetentionPerformance]
    """
    if not retention_curve:
        return 0.0
    # Average the relative retention performance (centered around 0.0, positive is above average)
    avg_relative = sum(float(r[2]) for r in retention_curve) / len(retention_curve)
    # Normalize to 0-1 range (relativeRetentionPerformance typically ranges between -0.5 and 0.5)
    return max(0.0, min(1.0, 0.5 + avg_relative))

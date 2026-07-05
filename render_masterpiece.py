import os
import sys
import asyncio
import json
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Thread safety
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from studio_core import (
    generate_anime_video,
    synthesize_hindi_audio,
    render_scene_60fps,
    get_ffmpeg_paths,
    get_audio_duration,
    scene_is_valid,
    async_call_with_retry
)

async def conform_clip(input_path: str, output_path: str) -> str:
    """Conforms clip to exactly 1080p, 30fps CFR, yuv420p, color-graded, and 48000Hz stereo AAC."""
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    tmp_output = Path(output_path).with_name(Path(output_path).stem + "_conform_tmp.mp4")
    
    # Uniform color grade filter: eq & colorbalance
    vf_filter = (
        "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
        "fps=30,eq=saturation=1.15:contrast=1.05:brightness=0.02,colorbalance=rs=0.03:gs=0.0:bs=-0.03,format=yuv420p"
    )
    
    cmd = [
        ffmpeg_cmd, "-y",
        "-threads", "1",
        "-i", input_path,
        "-vf", vf_filter,
        "-vsync", "cfr",
        "-c:v", "libx264", "-threads", "1", "-preset", "medium", "-crf", "16",
        "-profile:v", "high", "-level", "4.1",
        "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
        "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        str(tmp_output)
    ]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.communicate()
    
    if tmp_output.exists() and tmp_output.stat().st_size > 1000:
        if Path(output_path).exists():
            Path(output_path).unlink()
        tmp_output.rename(output_path)
        print(f"[Conform] Clip conformed successfully: {output_path}")
        return output_path
    else:
        print(f"[WARNING] Conform pass failed for {input_path}. Copying original.")
        shutil.copy(input_path, output_path)
        return output_path

def generate_title_image(text: str, out_path: str):
    """Draws a clean, centered title image using Pillow to avoid local FFmpeg font path errors."""
    img = Image.new("RGB", (1920, 1080), color=(26, 26, 46))
    draw = ImageDraw.Draw(img)
    font = None
    try:
        font = ImageFont.truetype("arial.ttf", 64)
    except IOError:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 64)
        except IOError:
            font = ImageFont.load_default()
            
    if hasattr(draw, "textbbox"):
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_w = right - left
        text_h = bottom - top
    else:
        text_w, text_h = 800, 80
        
    x = (1920 - text_w) // 2
    y = (1080 - text_h) // 2
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    img.save(out_path)

async def build_title_card(title_text: str, output_path: str):
    """Generates a conformed silent 1.5s title card clip."""
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    assets_dir = Path.cwd() / "assets"
    img_path = assets_dir / "title_image.png"
    generate_title_image(title_text, str(img_path))
    
    raw_title_card = assets_dir / "title_raw.mp4"
    
    cmd = [
        ffmpeg_cmd, "-y",
        "-loop", "1", "-i", str(img_path),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t", "1.5",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(raw_title_card)
    ]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await proc.communicate()
    
    await conform_clip(str(raw_title_card), output_path)
    
    if raw_title_card.exists():
        raw_title_card.unlink()
    if img_path.exists():
        img_path.unlink()

async def apply_chapter_transition(clip_a_path: str, clip_b_path: str, output_path: str) -> bool:
    """Applies a 0.4s cross-fade transition between two conformed clips with a whoosh sound effect."""
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    dur_a = get_audio_duration(clip_a_path)
    
    fade_duration = 0.4
    offset = max(0.1, dur_a - fade_duration)
    
    sfx_path = Path.cwd() / "assets" / "whoosh.mp3"
    if sfx_path.exists():
        print(f"[Transition] Found transition whoosh SFX. Weaving it at offset {offset:.2f}s...")
        offset_ms = int(offset * 1000)
        filter_complex = (
            f"[0:v][1:v]xfade=transition=fade:duration={fade_duration}:offset={offset}[outv]; "
            f"[2:a]adelay={offset_ms}|{offset_ms}[sfx]; "
            f"[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=0[amix_vocals]; "
            f"[amix_vocals][sfx]amix=inputs=2:duration=longest:dropout_transition=0[outa]"
        )
        cmd = [
            ffmpeg_cmd, "-y",
            "-i", clip_a_path,
            "-i", clip_b_path,
            "-i", str(sfx_path),
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "[outa]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]
    else:
        filter_complex = (
            f"[0:v][1:v]xfade=transition=fade:duration={fade_duration}:offset={offset}[outv]; "
            f"[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=0[outa]"
        )
        cmd = [
            ffmpeg_cmd, "-y",
            "-i", clip_a_path,
            "-i", clip_b_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "[outa]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await proc.communicate()
    return Path(output_path).exists() and Path(output_path).stat().st_size > 1000

async def enforce_target_duration(scene_paths: list, target_seconds: float = 270.0, tolerance: float = 5.0) -> list:
    """Enforces target runtime by padding with a freeze frame + silent audio or trimming conformed clips."""
    from studio_core import extract_last_frame
    
    total_duration = 0.0
    durations = []
    for path in scene_paths:
        d = get_audio_duration(path)
        durations.append(d)
        total_duration += d
        
    diff = target_seconds - total_duration
    print(f"[Duration Enforcer] Current duration: {total_duration:.2f}s, Target: {target_seconds:.2f}s, Diff: {diff:.2f}s")
    
    if abs(diff) <= tolerance:
        print("[Duration Enforcer] Duration is within tolerance. No changes made.")
        return scene_paths
        
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    assets_dir = Path.cwd() / "assets"
    
    if diff > 0:
        # Too short: pad the end of the video
        print(f"[Duration Enforcer] Video is too short by {diff:.2f}s. Padding last frame...")
        last_scene = scene_paths[-1]
        last_frame_path = assets_dir / "duration_pad_frame.png"
        pad_raw_path = assets_dir / "duration_pad_raw.mp4"
        pad_conformed_path = assets_dir / "conformed_scene_pad.mp4"
        
        try:
            extract_last_frame(last_scene, str(last_frame_path))
            cmd = [
                ffmpeg_cmd, "-y",
                "-loop", "1", "-i", str(last_frame_path),
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-t", f"{diff}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest", str(pad_raw_path)
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await proc.communicate()
            
            await conform_clip(str(pad_raw_path), str(pad_conformed_path))
            
            if pad_raw_path.exists():
                pad_raw_path.unlink()
            if last_frame_path.exists():
                last_frame_path.unlink()
                
            if pad_conformed_path.exists() and pad_conformed_path.stat().st_size > 1000:
                scene_paths.append(str(pad_conformed_path))
                print(f"[Duration Enforcer] Appended padding clip: {pad_conformed_path}")
            
        except Exception as e:
            print(f"[Duration Enforcer] Warning: padding failed: {e}")
            
    else:
        # Too long: trim the final scene
        trim_amount = abs(diff)
        print(f"[Duration Enforcer] Video is too long by {trim_amount:.2f}s. Trimming last scene...")
        last_scene = scene_paths[-1]
        last_duration = durations[-1]
        new_duration = max(1.0, last_duration - trim_amount)
        
        trimmed_path = assets_dir / "conformed_scene_trimmed_temp.mp4"
        
        cmd = [
            ffmpeg_cmd, "-y",
            "-ss", "0", "-t", f"{new_duration}",
            "-i", last_scene,
            "-c", "copy",
            str(trimmed_path)
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await proc.communicate()
        
        if trimmed_path.exists() and trimmed_path.stat().st_size > 1000:
            shutil.move(str(trimmed_path), last_scene)
            print(f"[Duration Enforcer] Last scene trimmed to {new_duration:.2f}s")
            
    return scene_paths

async def main():
    script_path = Path.cwd() / "assets" / "masterpiece_script.json"
    if not script_path.exists():
        print(f"Error: {script_path} does not exist. Run script helper first.")
        sys.exit(1)
        
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
        
    print(f"[Render Engine] Loaded script with {len(script)} scenes.")
    
    title_text = "Panchatantra Story"
    selected_hook = None
    if script and isinstance(script[0], dict):
        selected_hook = script[0].get("selected_hook")
    print(f"[Render Engine] Selected Hook style arm: {selected_hook}")
    
    title_conformed_path = Path.cwd() / "assets" / "conformed_scene_title.mp4"
    print("[Render Engine] Building Title Card...")
    await build_title_card(title_text, str(title_conformed_path))
    
    scene_files = []
    current_conditioning_image = None
    conformed_scene_paths = []
    
    for i, scene in enumerate(script, start=1):
        print(f"\n--- [Render Engine] Scene {i}/{len(script)} ---")
        safe_narration = scene['narration'].encode('ascii', errors='backslashreplace').decode('ascii')
        print(f"Narration: {safe_narration}")
        
        video_filename = f"raw_vid_{i}.mp4"
        audio_base = f"raw_aud_{i}"
        composite_base = f"final_scene_{i}"
        
        composite_path = Path.cwd() / "assets" / f"{composite_base}.mp4"
        conformed_base = f"conformed_scene_{i}"
        conformed_path = Path.cwd() / "assets" / f"{conformed_base}.mp4"
        
        # Every 5th scene, reset back to reference sheet to bound context drift
        if i % 5 == 1:
            ref_sheet = Path.cwd() / "assets" / "character_ref.png"
            if ref_sheet.exists():
                current_conditioning_image = str(ref_sheet)
                print(f"[Render Engine] Scene {i}: Resetting reference sheet to character_ref.png")
            else:
                current_conditioning_image = None
                print(f"[Render Engine] Scene {i}: Reference sheet not found, starting clean.")
        
        # QC Validity and Resumability check
        if scene_is_valid(str(conformed_path)):
            print(f"Conformed Scene {i} already rendered and conformed, skipping.")
            conformed_scene_paths.append(str(conformed_path))
            last_frame_path = Path.cwd() / "assets" / f"last_frame_{i}.png"
            try:
                from studio_core import extract_last_frame
                extract_last_frame(str(conformed_path), str(last_frame_path))
                current_conditioning_image = str(last_frame_path)
            except Exception as e:
                print(f"[Warning] Failed to extract last frame from conformed scene: {e}")
            continue
            
        if scene_is_valid(str(composite_path)):
            print(f"Scene {i} compiled but not conformed. Conforming...")
            await conform_clip(str(composite_path), str(conformed_path))
            conformed_scene_paths.append(str(conformed_path))
            last_frame_path = Path.cwd() / "assets" / f"last_frame_{i}.png"
            try:
                from studio_core import extract_last_frame
                extract_last_frame(str(conformed_path), str(last_frame_path))
                current_conditioning_image = str(last_frame_path)
            except Exception as e:
                print(f"[Warning] Failed to extract last frame from conformed scene: {e}")
            continue
            
        print("Generating audio assets...")
        lang = scene.get("language", "hi")
        audio_res = await synthesize_hindi_audio(scene["narration"], audio_base, scene_idx=i, language=lang)
        
        duration = get_audio_duration(audio_res["audio_file"])
        print(f"Audio duration: {duration:.2f}s")
        
        is_hero = True
        
        print(f"Generating visual assets (is_hero: {is_hero})...")
        raw_vid = await async_call_with_retry(
            generate_anime_video, scene["scene_prompt"], video_filename, duration=duration, is_hero=is_hero, conditioning_image=current_conditioning_image
        )
        
        print("Compositing to 60 FPS...")
        final_scene = await render_scene_60fps(
            raw_vid, audio_res["audio_file"], audio_res["subtitle_file"], composite_base
        )
        
        # Clean raw temporary assets to save space
        try:
            for temp_file in [raw_vid, audio_res["audio_file"], audio_res["subtitle_file"]]:
                p = Path(temp_file)
                if p.exists():
                    p.unlink()
            srt_temp = Path(audio_res["subtitle_file"]).with_suffix(".srt")
            if srt_temp.exists():
                srt_temp.unlink()
        except Exception as ce:
            print(f"[Warning] Failed to clean temp files: {ce}")
            
        await conform_clip(final_scene["video_file"], str(conformed_path))
        conformed_scene_paths.append(str(conformed_path))
        
        last_frame_path = Path.cwd() / "assets" / f"last_frame_{i}.png"
        try:
            from studio_core import extract_last_frame
            extract_last_frame(str(conformed_path), str(last_frame_path))
            current_conditioning_image = str(last_frame_path)
        except Exception as e:
            print(f"[Warning] Failed to extract last frame: {e}")
            current_conditioning_image = None
            
        print(f"Scene {i} compiled and conformed successfully.")
        
    # Enforce Target Runtime
    conformed_scene_paths = await enforce_target_duration(conformed_scene_paths, target_seconds=270.0, tolerance=5.0)
    
    # Chapter boundary cross-fades
    final_scene_files = []
    if title_conformed_path.exists():
        final_scene_files.append(f"file '{title_conformed_path.name}'\n")
        
    i = 0
    manifest_scenes = []
    while i < len(conformed_scene_paths):
        scene_idx = i + 1
        current_conformed = Path(conformed_scene_paths[i])
        
        if scene_idx % 5 == 0 and i < len(conformed_scene_paths) - 1:
            next_scene_idx = scene_idx + 1
            next_conformed = Path(conformed_scene_paths[i + 1])
            transition_base = f"transition_scene_{scene_idx}_{next_scene_idx}"
            transition_path = Path.cwd() / "assets" / f"{transition_base}.mp4"
            transition_conformed = Path.cwd() / "assets" / f"conformed_{transition_base}.mp4"
            
            print(f"[Render Engine] Applying cross-fade transition between Chapter {scene_idx//5} and {scene_idx//5 + 1}...")
            ok = await apply_chapter_transition(str(current_conformed), str(next_conformed), str(transition_path))
            if ok:
                await conform_clip(str(transition_path), str(transition_conformed))
                if transition_path.exists():
                    transition_path.unlink()
                
                final_scene_files.append(f"file '{transition_conformed.name}'\n")
                manifest_scenes.append({"scene": scene_idx, "tier_used": "transition", "fallback_reason": None})
                i += 2
                continue
                
        final_scene_files.append(f"file '{current_conformed.name}'\n")
        manifest_scenes.append({"scene": scene_idx, "tier_used": "pose_or_parallax", "fallback_reason": None})
        i += 1
        
    print("\n[Render Engine] Concatenating final movie...")
    list_file = Path.cwd() / "assets" / "concat.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        f.writelines(final_scene_files)
        
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    output_path = Path.cwd() / "assets" / "FINAL_MASTERPIECE.mp4"
    
    cmd_concat = [
        ffmpeg_cmd, "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy",
        "-metadata", "copyright=Owned by Creator",
        "-metadata", "title=Premium Kids Animation",
        str(output_path)
    ]
    
    proc = await asyncio.create_subprocess_exec(*cmd_concat)
    await proc.communicate()
    
    if list_file.exists():
        list_file.unlink()
        
    # Write Manifest
    manifest_path = Path.cwd() / "assets" / "render_manifest.json"
    manifest_data = {
        "video_id": "FINAL_MASTERPIECE",
        "selected_hook": selected_hook,
        "scenes": manifest_scenes
    }
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest_data, mf, indent=2)
        
    print(f"\n[Render Engine] DONE! Movie compiled as {output_path} and manifest saved to {manifest_path}.")

if __name__ == "__main__":
    asyncio.run(main())

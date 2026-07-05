import os
import sys
import asyncio
import json
import subprocess
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

# Conforming and utility methods shared with render_masterpiece
from render_masterpiece import (
    conform_clip,
    build_title_card,
    apply_chapter_transition,
    enforce_target_duration
)

async def build_masterpiece(topic: str = "magical forest adventure and friendship", output_filename: str = "FINAL_MASTERPIECE.mp4", duration: int = 4):
    print(f"[Orchestrator] Starting Studio 5.0 Production Pipeline for topic: {topic}...")
    base_slug = Path(output_filename).stem
    
    # 1. Generate script with custom duration
    script_output = Path.cwd() / "assets" / f"masterpiece_script_{base_slug}.json"
    
    if script_output.exists():
        print(f"[Orchestrator] Script file already exists at {script_output}. Skipping script generation.")
    else:
        print("[Orchestrator] Launching script generator subprocess...")
        cmd = [
            ".venv\\Scripts\\python.exe", "studio_script_helper.py",
            "--action", "generate",
            "--topic", topic,
            "--duration", str(duration),
            "--output", str(script_output)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.stdout:
            safe_stdout = res.stdout.encode('ascii', errors='backslashreplace').decode('ascii')
            print(safe_stdout)
        if res.stderr:
            safe_stderr = res.stderr.encode('ascii', errors='backslashreplace').decode('ascii')
            print(safe_stderr, file=sys.stderr)
        if res.returncode != 0:
            raise subprocess.CalledProcessError(res.returncode, cmd, output=res.stdout, stderr=res.stderr)
    
    with open(script_output, "r", encoding="utf-8") as f:
        script = json.load(f)
        
    print(f"[Orchestrator] Script loaded successfully with {len(script)} scenes.")
    
    # Check if we have a title to render a title card
    title_text = topic.title()
    selected_hook = None
    if script and isinstance(script[0], dict):
        selected_hook = script[0].get("selected_hook")
    print(f"[Orchestrator] Selected Hook style arm: {selected_hook}")
    
    title_conformed_path = Path.cwd() / "assets" / f"conformed_scene_title_{base_slug}.mp4"
    print("[Orchestrator] Building Title Card...")
    await build_title_card(title_text, str(title_conformed_path))
    
    scene_files = []
    current_conditioning_image = None
    conformed_scene_paths = []
    
    # 2. Render each scene sequentially
    for i, scene in enumerate(script, start=1):
        print(f"[Orchestrator] Rendering Scene {i}/{len(script)}...")
        safe_narration = scene['narration'].encode('ascii', errors='backslashreplace').decode('ascii')
        print(f" Narration: {safe_narration}")
        
        video_filename = f"raw_vid_{base_slug}_{i}.mp4"
        audio_base = f"raw_aud_{base_slug}_{i}"
        composite_base = f"final_scene_{base_slug}_{i}"
        
        composite_path = Path.cwd() / "assets" / f"{composite_base}.mp4"
        conformed_base = f"conformed_scene_{base_slug}_{i}"
        conformed_path = Path.cwd() / "assets" / f"{conformed_base}.mp4"
        
        # Every 5th scene, reset back to reference sheet to bound context drift
        if i % 5 == 1:
            ref_sheet = Path.cwd() / "assets" / "character_ref.png"
            if ref_sheet.exists():
                current_conditioning_image = str(ref_sheet)
                print(f"[Orchestrator] Scene {i}: Resetting reference sheet to character_ref.png")
            else:
                current_conditioning_image = None
                print(f"[Orchestrator] Scene {i}: Reference sheet not found, starting clean.")
        
        if scene_is_valid(str(conformed_path)):
            print(f"Conformed Scene {i} already rendered and conformed, skipping.")
            conformed_scene_paths.append(str(conformed_path))
            last_frame_path = Path.cwd() / "assets" / f"last_frame_{base_slug}_{i}.png"
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
            last_frame_path = Path.cwd() / "assets" / f"last_frame_{base_slug}_{i}.png"
            try:
                from studio_core import extract_last_frame
                extract_last_frame(str(conformed_path), str(last_frame_path))
                current_conditioning_image = str(last_frame_path)
            except Exception as e:
                print(f"[Warning] Failed to extract last frame from conformed scene: {e}")
            continue
            
        # Generate assets
        lang = scene.get("language", "hi")
        audio_res = await synthesize_hindi_audio(scene["narration"], audio_base, scene_idx=i, language=lang)
        duration = get_audio_duration(audio_res["audio_file"])
        
        is_hero = False
        raw_vid = await async_call_with_retry(
            generate_anime_video, scene["scene_prompt"], video_filename, duration=duration, is_hero=is_hero, conditioning_image=current_conditioning_image
        )
        
        # Composite via CPU to 60 FPS
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
        
        # Extract last frame from conformed scene for next generation call
        last_frame_path = Path.cwd() / "assets" / f"last_frame_{base_slug}_{i}.png"
        try:
            from studio_core import extract_last_frame
            extract_last_frame(str(conformed_path), str(last_frame_path))
            current_conditioning_image = str(last_frame_path)
        except Exception as e:
            print(f"[Warning] Failed to extract last frame: {e}")
            current_conditioning_image = None
            
        print(f"Scene {i} compiled and conformed successfully.")
        
    # Enforce Target Runtime
    # If duration parameter is less than 4, let's scale the target_seconds enforcer too
    target_secs = 270.0
    if duration <= 1:
        target_secs = 90.0
    elif duration == 2:
        target_secs = 140.0
    elif duration == 3:
        target_secs = 200.0
        
    conformed_scene_paths = await enforce_target_duration(conformed_scene_paths, target_seconds=target_secs, tolerance=5.0)
    
    # Weave Chapter Transitions
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
            transition_base = f"transition_scene_{base_slug}_{scene_idx}_{next_scene_idx}"
            transition_path = Path.cwd() / "assets" / f"{transition_base}.mp4"
            transition_conformed = Path.cwd() / "assets" / f"conformed_{transition_base}.mp4"
            
            print(f"[Orchestrator] Applying cross-fade transition between Chapter {scene_idx//5} and {scene_idx//5 + 1}...")
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
        
    # 3. Concatenate into Final Movie
    print("[Orchestrator] Assembling Final Movie...")
    list_file = Path.cwd() / "assets" / f"concat_{base_slug}.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        f.writelines(final_scene_files)
        
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    output_path = Path.cwd() / "assets" / output_filename
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
    if script_output.exists():
        script_output.unlink()
        
    # Write Render Manifest
    manifest_path = Path.cwd() / "assets" / f"render_manifest_{base_slug}.json"
    manifest_data = {
        "video_id": base_slug,
        "selected_hook": selected_hook,
        "scenes": manifest_scenes
    }
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest_data, mf, indent=2)
        
    print(f"[Orchestrator] DONE! Video saved as {output_path}. Render manifest saved as {manifest_path}.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="magical forest adventure and friendship")
    parser.add_argument("--output", type=str, default="FINAL_MASTERPIECE.mp4")
    parser.add_argument("--duration", type=int, default=4)
    args = parser.parse_args()
    
    asyncio.run(build_masterpiece(args.topic, args.output, args.duration))

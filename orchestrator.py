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
    enforce_target_duration,
    probe_has_video_stream
)

import glob

def clean_previous_assets(base_slug: str = None):
    """Deletes ALL previous cached assets to ensure a completely fresh run."""
    assets_dir = Path.cwd() / "assets"
    out_dir = Path.cwd() / "out"
    
    patterns = [
        "conformed_scene_*.mp4",
        "conformed_transition_*.mp4",
        "final_scene_*.mp4",
        "raw_vid_*.mp4",
        "raw_aud_*.*",
        "last_frame_*.png",
        "transition_*.mp4",
        "masterpiece_script_*.json",
        "concat_*.txt",
        "title_raw.mp4",
        "title_image.png",
        "duration_pad_*.png",
        "duration_pad_*.mp4",
    ]
    
    deleted = 0
    for pattern in patterns:
        for f in assets_dir.glob(pattern):
            try:
                f.unlink()
                deleted += 1
            except Exception as e:
                print(f"[Cleanup] Could not delete {f.name}: {e}")
    
    # Clean output directory
    if out_dir.exists():
        for f in out_dir.glob("*.mp4"):
            try:
                f.unlink()
                deleted += 1
            except Exception as e:
                print(f"[Cleanup] Could not delete {f.name}: {e}")
    
    print(f"[Cleanup] Deleted {deleted} cached files. Starting fresh.")

DEFAULT_ORIGINALITY_THRESHOLD = 0.85

async def build_masterpiece(topic: str = "magical forest adventure and friendship", output_filename: str = "FINAL_MASTERPIECE.mp4", duration: int = 4, clean: bool = False, force: bool = False):
    print(f"[Orchestrator] Starting Studio 5.0 Production Pipeline for topic: {topic}...")
    base_slug = Path(output_filename).stem
    
    # 0. Clean ALL previous cached assets (only when --clean flag is set)
    if clean:
        clean_previous_assets(base_slug)
    
    # Ensure required directories always exist
    (Path.cwd() / "assets").mkdir(exist_ok=True)
    (Path.cwd() / "out").mkdir(exist_ok=True)
    
    # 1. Generate script with custom duration
    script_output = Path.cwd() / "assets" / f"masterpiece_script_{base_slug}.json"
    
    if script_output.exists():
        print(f"[Orchestrator] Script file already exists at {script_output}. Skipping script generation.")
    else:
        # Originality check: block or warn if topic is too similar to recent videos
        try:
            from db import get_db, init_db, check_originality, store_script
            try:
                db = get_db()
            except Exception:
                init_db()
                db = get_db()
            try:
                originality = check_originality(topic, "", db, threshold=DEFAULT_ORIGINALITY_THRESHOLD)
                if not originality["is_original"]:
                    warning_msg = (
                        f"[ORIGINALITY GUARD] Topic '{topic}' is too similar to past topic "
                        f"'{originality['closest_topic']}' (similarity: {originality['closest_score']:.2f} >= {DEFAULT_ORIGINALITY_THRESHOLD})."
                    )
                    print(f"\n{warning_msg}")
                    if not force:
                        raise ValueError(
                            f"{warning_msg} Aborting to protect against YouTube mass-produced content penalty. "
                            f"Specify a different topic or use --force to proceed anyway."
                        )
                    else:
                        print("[ORIGINALITY GUARD] --force flag supplied. Proceeding despite similarity warning.\n")
                else:
                    print(f"[Orchestrator] Originality check passed (closest match: {originality['closest_score']:.2f} < {DEFAULT_ORIGINALITY_THRESHOLD}).")
            finally:
                db.close()
        except ValueError:
            raise
        except Exception as e:
            print(f"[Orchestrator] Originality check skipped: {e}")
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
    
    # Store script in originality database for future duplicate detection
    try:
        from db import get_db, init_db, store_script
        try:
            db = get_db()
        except Exception:
            init_db()
            db = get_db()
        try:
            script_text = json.dumps([s.get("narration", "") for s in script[:10]])
            store_script(topic, script_text, db)
            print("[Orchestrator] Script stored in originality database.")
        finally:
            db.close()
    except Exception as e:
        print(f"[Orchestrator] Script storage skipped: {e}")
    
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
    # Load existing manifest if present to preserve cached scene results
    manifest_path = Path.cwd() / "assets" / f"render_manifest_{base_slug}.json"
    cached_scenes = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                old_manifest = json.load(f)
                for s in old_manifest.get("scenes", []):
                    if isinstance(s, dict) and "scene" in s:
                        cached_scenes[s["scene"]] = s
        except Exception:
            pass

    current_conditioning_image = None
    conformed_scene_paths = []
    scene_results = {}
    
    # 2. Render each scene sequentially
    for i, scene in enumerate(script, start=1):
        print(f"[Orchestrator] Rendering Scene {i}/{len(script)}...")
        
        # Guard: ensure narration and scene_prompt are never empty
        if not scene.get('narration') or not scene['narration'].strip():
            scene['narration'] = f"Aur phir {topic} ki kahani mein ek naya aur rochak drishya saamne aaya, drishya {i}."
            print(f"[Orchestrator] WARNING: Scene {i} had empty narration. Using fallback.")
        if not scene.get('scene_prompt') or not scene['scene_prompt'].strip():
            scene['scene_prompt'] = f"A beautiful cartoon scene of {topic}, scene {i}, vibrant colors, happy characters, detailed background, cinematic lighting."
            print(f"[Orchestrator] WARNING: Scene {i} had empty scene_prompt. Using fallback.")
        
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
            if i in cached_scenes:
                scene_results[i] = cached_scenes[i]
            else:
                scene_results[i] = {"scene": i, "tier_attempted": 2, "tier_used": 2, "fallback_reason": None}
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
            if i in cached_scenes:
                scene_results[i] = cached_scenes[i]
            else:
                scene_results[i] = {"scene": i, "tier_attempted": 2, "tier_used": 2, "fallback_reason": None}
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
        voice = scene.get("voice")
        rate = scene.get("rate")
        pitch = scene.get("pitch")
        audio_res = await async_call_with_retry(
            synthesize_hindi_audio,
            scene["narration"], audio_base, scene_idx=i, language=lang,
            voice=voice, rate=rate, pitch=pitch,
            max_retries=3, base_delay=2.0
        )
        audio_dur = get_audio_duration(audio_res["audio_file"])
        
        # Select hero beats (Tier 1) for 1-3 scenes (start, middle, near end)
        is_hero = scene.get("is_hero")
        if is_hero is None:
            if len(script) >= 15:
                is_hero = (i in [3, len(script) // 2, len(script) - 2])
            else:
                is_hero = (i == len(script) // 2)
            
        raw_vid = await async_call_with_retry(
            generate_anime_video, scene["scene_prompt"], video_filename, duration=audio_dur, is_hero=is_hero, conditioning_image=current_conditioning_image
        )
        
        # Collect metadata from VideoResult
        tier_attempted = getattr(raw_vid, "tier_attempted", 2)
        tier_used = getattr(raw_vid, "tier_used", 2)
        fallback_reason = getattr(raw_vid, "fallback_reason", None)
        scene_results[i] = {
            "scene": i,
            "tier_attempted": tier_attempted,
            "tier_used": tier_used,
            "fallback_reason": fallback_reason
        }
        
        # Composite via CPU to 60 FPS
        bgm_file = scene.get("bgm_file")
        sfx_file = scene.get("sfx_file")
        final_scene = await render_scene_60fps(
            raw_vid, audio_res["audio_file"], audio_res["subtitle_file"], composite_base,
            bgm_path=bgm_file, sfx_path=sfx_file
        )
        
        # Validate compositor output before proceeding
        composite_output = final_scene.get("video_file", "")
        if not scene_is_valid(composite_output, min_duration_s=2.0):
            print(f"[ERROR] Scene {i} compositor produced invalid output: {composite_output}")
            # Attempt a simpler re-composite without BGM/SFX
            print(f"[Orchestrator] Retrying scene {i} composite without BGM/SFX...")
            final_scene = await render_scene_60fps(
                raw_vid, audio_res["audio_file"], audio_res["subtitle_file"], composite_base
            )
            if not scene_is_valid(final_scene.get("video_file", ""), min_duration_s=2.0):
                raise RuntimeError(f"[CRITICAL] Scene {i} failed compositor: output video is invalid or missing ({final_scene.get('video_file', '')}).")
        
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
    if title_conformed_path.exists() and probe_has_video_stream(str(title_conformed_path)):
        final_scene_files.append(f"file '{title_conformed_path.name}'\n")
    elif title_conformed_path.exists():
        print("[WARNING] Title card has no video stream — skipping from concat.")
        
    i = 0
    manifest_scenes = []
    while i < len(conformed_scene_paths):
        scene_idx = i + 1
        current_conformed = Path(conformed_scene_paths[i])
        
        # Validate this scene has a video stream before including
        if not probe_has_video_stream(str(current_conformed)):
            print(f"[WARNING] Scene {scene_idx} has no video stream — skipping.")
            i += 1
            continue
        
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
                i += 2
                continue
                
        final_scene_files.append(f"file '{current_conformed.name}'\n")
        res = scene_results.get(scene_idx, {
            "scene": scene_idx,
            "tier_attempted": 2,
            "tier_used": 2,
            "fallback_reason": None
        })
        manifest_scenes.append(res)
        i += 1
        
    # 3. Concatenate into Final Movie
    print("[Orchestrator] Assembling Final Movie...")
    list_file = Path.cwd() / "assets" / f"concat_{base_slug}.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        f.writelines(final_scene_files)
        
    ffmpeg_cmd, _ = get_ffmpeg_paths()
    output_path = Path.cwd() / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd_concat = [
        ffmpeg_cmd, "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "16",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart",
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
    tier_1_count = sum(1 for s in manifest_scenes if s.get("tier_used") == 1)
    tier_2_count = sum(1 for s in manifest_scenes if s.get("tier_used") == 2)
    tier_3_count = sum(1 for s in manifest_scenes if s.get("tier_used") == 3)
    
    manifest_data = {
        "video_id": base_slug,
        "selected_hook": selected_hook,
        "scenes": manifest_scenes,
        "tier_1_count": tier_1_count,
        "tier_2_count": tier_2_count,
        "tier_3_count": tier_3_count
    }
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest_data, mf, indent=2)
        
    # Pre-publish validation: comprehensive check before declaring success
    if output_path.exists():
        has_video = probe_has_video_stream(str(output_path))
        file_size = output_path.stat().st_size
        final_duration = get_audio_duration(str(output_path))
        
        issues = []
        if not has_video:
            issues.append("NO video stream detected")
        if file_size < 5_000_000:  # <5MB is suspiciously small for a multi-minute video
            issues.append(f"File size too small ({file_size / 1024 / 1024:.1f}MB)")
        if final_duration < target_secs * 0.5:
            issues.append(f"Duration too short ({final_duration:.1f}s vs target {target_secs:.1f}s)")
        if final_duration > target_secs * 2.0:
            issues.append(f"Duration too long ({final_duration:.1f}s vs target {target_secs:.1f}s)")
            
        if issues:
            print(f"[Orchestrator] [WARNING] Pre-publish validation issues: {'; '.join(issues)}")
            print(f"[Orchestrator] Video at {output_path} may need manual review before uploading.")
        else:
            print(f"[Orchestrator] [OK] DONE! Video saved as {output_path}")
            print(f"  Duration: {final_duration:.1f}s | Size: {file_size / 1024 / 1024:.1f}MB | Manifest: {manifest_path}")
    else:
        print(f"[Orchestrator] [ERROR] Final video was NOT created at {output_path}!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="magical forest adventure and friendship")
    parser.add_argument("--output", type=str, default="FINAL_MASTERPIECE.mp4")
    parser.add_argument("--duration", type=int, default=4)
    parser.add_argument("--clean", action="store_true", help="Delete all cached assets and start from scratch")
    parser.add_argument("--force", action="store_true", help="Force script generation even if topic is similar to past videos")
    args = parser.parse_args()
    
    asyncio.run(build_masterpiece(args.topic, args.output, args.duration, clean=args.clean, force=args.force))

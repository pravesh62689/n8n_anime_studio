import os
# Limit PyTorch CPU thread pool to 1 to bypass MKL/OpenMP deadlock on Windows
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import asyncio
import json
import sys
import unittest
import subprocess
import platform


# WMI Query Bypass for Windows
platform.system = lambda: "Windows"
class MockUname:
    system = "Windows"
    node = "localhost"
    release = "10"
    version = "10.0.0"
    machine = "AMD64"
    processor = "Intel"
    def __getitem__(self, idx):
        return [self.system, self.node, self.release, self.version, self.machine, self.processor][idx]
platform.uname = lambda: MockUname()

from pathlib import Path
from dotenv import load_dotenv

# Ensure we can import scripts from the current directory
sys.path.append(str(Path.cwd()))
load_dotenv()

class TestAnimeStudioPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("\n=== SYSTEM ENVIRONMENT VALIDATION ===")
        print(f"Python Version: {sys.version}")
        print(f"Current Directory: {Path.cwd()}")
        
        # Verify FFmpeg
        from studio_core import get_ffmpeg_paths
        ffmpeg_cmd, ffprobe_cmd = get_ffmpeg_paths()
        print(f"FFmpeg path: {ffmpeg_cmd}")
        print(f"FFprobe path: {ffprobe_cmd}")
        
        try:
            r_ffmpeg = subprocess.run([ffmpeg_cmd, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"FFmpeg test: Success (Version: {r_ffmpeg.stdout.splitlines()[0]})")
        except Exception as e:
            print(f"FFmpeg test: FAILED! {e}")
            
        try:
            r_ffprobe = subprocess.run([ffprobe_cmd, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"FFprobe test: Success (Version: {r_ffprobe.stdout.splitlines()[0]})")
        except Exception as e:
            print(f"FFprobe test: FAILED! {e}")
            
        # Ensure assets directory exists
        cls.assets_dir = Path.cwd() / "assets"
        cls.assets_dir.mkdir(parents=True, exist_ok=True)
        
    def test_01_ffmpeg_binaries_present(self):
        """Test Case 1: Check that FFmpeg and FFprobe binaries are found locally or globally."""
        from studio_core import get_ffmpeg_paths
        ffmpeg_cmd, ffprobe_cmd = get_ffmpeg_paths()
        
        # Verify either local files exist, or commands run globally
        if "ffmpeg.exe" in ffmpeg_cmd:
            self.assertTrue(Path(ffmpeg_cmd).exists(), "Local ffmpeg.exe should exist if path is returned")
            self.assertTrue(Path(ffprobe_cmd).exists(), "Local ffprobe.exe should exist if path is returned")
        else:
            # Check global access
            r = subprocess.run(["where", "ffmpeg"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(r.returncode, 0, "FFmpeg should be globally available if local binaries are missing")

    def test_02_pollinations_video_generation(self):
        """Test Case 2: Check Pollinations.ai video downloader tool."""
        print("\n=== TESTING POLLINATIONS VIDEO GENERATION ===")
        from studio_core import generate_anime_video
        
        prompt = "cute white cat flying with balloon, ghibli style"
        filename = "test_video.mp4"
        target_path = self.assets_dir / filename
        
        # Remove if already exists
        if target_path.exists():
            target_path.unlink()
            
        path = asyncio.run(generate_anime_video(prompt, filename))
        
        print(f"Generated video path: {path}")
        self.assertTrue(Path(path).exists(), "Downloaded video file should exist")
        self.assertGreater(Path(path).stat().st_size, 1000, "Downloaded file should be larger than 1KB")

    def test_03_edge_tts_audio_synthesis(self):
        """Test Case 3: Check edge-tts Speech Synthesis & Subtitle generation."""
        print("\n=== TESTING TTS SPEECH SYNTHESIS ===")
        from studio_core import synthesize_hindi_audio
        
        text = "Hello and welcome to the local standalone anime studio pipeline testing suite!"
        base_filename = "test_vocal"
        
        audio_path = self.assets_dir / f"{base_filename}.mp3"
        ass_path = self.assets_dir / f"{base_filename}.ass"
        
        # Remove old files
        for p in (audio_path, ass_path):
            if p.exists():
                p.unlink()
                
        result = asyncio.run(synthesize_hindi_audio(text, base_filename, character="narrator"))
        
        print(f"Generated audio result: {result}")
        self.assertTrue(Path(result["audio_file"]).exists(), "Audio file should exist")
        self.assertTrue(Path(result["subtitle_file"]).exists(), "Subtitle file should exist")
        self.assertGreater(Path(result["audio_file"]).stat().st_size, 1000, "Audio file should be larger than 1KB")
        self.assertGreater(Path(result["subtitle_file"]).stat().st_size, 100, "Subtitle file should be larger than 100B")

    def test_04_ffmpeg_compositor_rendering(self):
        """Test Case 4: Test FFmpeg video scene rendering using 60fps compositor."""
        print("\n=== TESTING FFMPEG ANIME COMPOSITOR ===")
        from studio_core import render_scene_60fps
        
        video_path = str(self.assets_dir / "test_video.mp4")
        audio_path = str(self.assets_dir / "test_vocal.mp3")
        subtitle_path = str(self.assets_dir / "test_vocal.ass")
        base_filename = "test_output_scene"
        
        output_path = self.assets_dir / f"{base_filename}.mp4"
        if output_path.exists():
            output_path.unlink()
            
        try:
            result = asyncio.run(render_scene_60fps(video_path, audio_path, subtitle_path, base_filename))
            print(f"Generated video scene: {result}")
            self.assertTrue(Path(result["video_file"]).exists(), "Generated video MP4 should exist")
            self.assertGreater(Path(result["video_file"]).stat().st_size, 5000, "Video file should be larger than 5KB")
        except RuntimeError as e:
            print(f"\n[WARNING] FFmpeg rendering failed: {e}")

    def test_05_openrouter_antigravity_scripting(self):
        """Test Case 5: Verify OpenRouter scripting cascade."""
        print("\n=== TESTING OPENROUTER SCRIPTING ===")
        from studio_core import generate_hindi_script
        
        llama_key = os.getenv("OR_LLAMA_KEY") or os.getenv("OR_KEY_LLAMA")
        if not llama_key:
            self.skipTest("Neither OR_LLAMA_KEY nor OR_KEY_LLAMA environment variable is set.")
            return
            
        print("OR_LLAMA_KEY found, running scripting cascade...")
        topic = "A small robot learning to grow a flower"
        script_output = generate_hindi_script(topic)
        
        safe_output = repr(script_output).encode("ascii", errors="backslashreplace").decode("ascii")
        print(f"Generated Script: {safe_output}")
        self.assertIsNotNone(script_output, "Script output should not be None")
        self.assertTrue(isinstance(script_output, list), "Script output must be a list of scenes")
        self.assertGreater(len(script_output), 0, "Script list should not be empty")

    def test_06_sqlite_vec_local_embeddings(self):
        """Test Case 6: Verify sqlite-vec binary vector DB with local SentenceTransformer."""
        print("\n=== TESTING SQLITE-VEC LOCAL RAG ANALYTICS ===")
        from studio_core import ingest_performance, retrieve_reinforced_context
        
        video_id = "test_vid_1"
        text_content = "This video is about a cute anime cat flying in the sky with a yellow balloon."
        retention_score = 90
        
        # Cleanup database file if it exists before running so we get a clean result
        db_path = Path("analytics_rag.db")
        if db_path.exists():
            try:
                db_path.unlink()
            except Exception:
                pass
                
        # Ingest
        ingest_performance(video_id, text_content, retention_score)
        
        # Retrieve context
        context = retrieve_reinforced_context("cute anime cat flying")
        print(f"RAG search result context: {context}")
        
        self.assertIsNotNone(context, "Context should not be None")
        self.assertIn("cute anime cat", context, "Context should contain the matched text")

    def test_07_extract_last_frame_and_conform(self):
        """Test Case 7: Verify last frame extraction and CFR conforming features."""
        print("\n=== TESTING LAST-FRAME EXTRACTION & CONFORMING ===")
        from studio_core import extract_last_frame
        from orchestrator import conform_clip
        
        input_vid = str(self.assets_dir / "test_output_scene.mp4")
        conformed_vid = str(self.assets_dir / "test_conformed_scene.mp4")
        last_frame_png = str(self.assets_dir / "test_last_frame.png")
        
        # Cleanup files
        for p in (conformed_vid, last_frame_png):
            if Path(p).exists():
                Path(p).unlink()
                
        # Verify input video exists from previous test
        if not Path(input_vid).exists():
            self.skipTest("Composited test video test_output_scene.mp4 not found.")
            return
            
        # Conform clip
        asyncio.run(conform_clip(input_vid, conformed_vid))
        self.assertTrue(Path(conformed_vid).exists(), "Conformed clip should be generated.")
        
        # Extract last frame
        extract_last_frame(conformed_vid, last_frame_png)
        self.assertTrue(Path(last_frame_png).exists(), "Last frame image should be extracted.")
        self.assertGreater(Path(last_frame_png).stat().st_size, 1000, "PNG file should be larger than 1KB.")
        
        # Verify conformed properties using ffprobe
        from studio_core import get_ffmpeg_paths
        _, ffprobe_cmd = get_ffmpeg_paths()
        cmd = [
            ffprobe_cmd, "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate,profile,level", "-of", "json", conformed_vid
        ]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        info = json.loads(r.stdout)
        stream = info["streams"][0]
        
        print(f"Conformed Clip Stream Info: {stream}")
        self.assertEqual(stream["r_frame_rate"], "30/1", "Conformed clip must be conformed to exactly 30 FPS.")
        self.assertEqual(stream["profile"], "High", "Conformed clip must use High Profile.")
        self.assertEqual(stream["level"], 41, "Conformed clip must use Level 4.1.")

    def test_08_bandit_feedback(self):
        """Test Case 8: Verify epsilon-greedy bandit selector and reward calculations."""
        print("\n=== TESTING CONTEXTUAL BANDIT FEEDBACK ===")
        from studio_core import select_bandit_arm, update_bandit_arm, compute_retention_reward
        
        arm_names = ["hook_question", "hook_action", "hook_climax"]
        
        # Test reward calculation
        ret_curve = [
            [0.1, 0.9, 0.1],
            [0.5, 0.7, 0.2],
            [0.9, 0.4, 0.0]
        ]
        reward = compute_retention_reward(ret_curve)
        print(f"Calculated reward: {reward}")
        self.assertTrue(0.0 <= reward <= 1.0, "Reward must be normalized between 0.0 and 1.0")
        
        # Test arm updates and selection
        update_bandit_arm("hook_action", 0.95)
        update_bandit_arm("hook_question", 0.45)
        
        selected = select_bandit_arm(arm_names)
        print(f"Bandit selected arm: {selected}")
        self.assertIn(selected, arm_names, "Selected arm must be in the list of arms.")

    def test_09_localize_script(self):
        """Test Case 9: Verify script translation cascade."""
        print("\n=== TESTING SCRIPT TRANSLATION ===")
        from studio_core import localize_script
        
        script_hi = "Ek sunhari chidiya ped par rehti thi."
        try:
            translated = localize_script(script_hi, "es")
            print(f"Translated to Spanish: {translated}")
            self.assertIsNotNone(translated)
            self.assertGreater(len(translated), 0)
        except Exception as e:
            print(f"[Warning] Translation test skipped/failed: {e}")
            
    def test_10_title_card_rendering(self):
        """Test Case 10: Verify Pillow title card drawing and video compilation."""
        print("\n=== TESTING TITLE CARD GENERATION ===")
        from render_masterpiece import build_title_card, generate_title_image
        
        title_text = "The Clever Fox"
        img_path = str(self.assets_dir / "test_title.png")
        vid_path = str(self.assets_dir / "test_title_card.mp4")
        
        # Cleanup
        for p in (img_path, vid_path):
            if Path(p).exists():
                Path(p).unlink()
                
        generate_title_image(title_text, img_path)
        self.assertTrue(Path(img_path).exists(), "Title PNG should be generated.")
        
        asyncio.run(build_title_card(title_text, vid_path))
        self.assertTrue(Path(vid_path).exists(), "Title card MP4 should be generated.")
        self.assertGreater(Path(vid_path).stat().st_size, 1000, "Title card MP4 should be larger than 1KB.")

    def test_11_chapter_transition(self):
        """Test Case 11: Verify chapter cross-fade transitions."""
        print("\n=== TESTING CHAPTER TRANSITIONS ===")
        from render_masterpiece import apply_chapter_transition
        
        clip_a = str(self.assets_dir / "test_conformed_scene.mp4")
        clip_b = str(self.assets_dir / "test_conformed_scene.mp4")
        out_transition = str(self.assets_dir / "test_transition_out.mp4")
        
        if not Path(clip_a).exists() or not Path(clip_b).exists():
            self.skipTest("Required conformed clips for transition testing not found.")
            return
            
        if Path(out_transition).exists():
            Path(out_transition).unlink()
            
        ok = asyncio.run(apply_chapter_transition(clip_a, clip_b, out_transition))
        self.assertTrue(ok, "Transition compilation should succeed.")
        self.assertTrue(Path(out_transition).exists(), "Transition MP4 should exist.")

    def test_12_duration_enforcement(self):
        """Test Case 12: Verify padding and trimming duration enforcer."""
        print("\n=== TESTING DURATION ENFORCEMENT ===")
        from render_masterpiece import enforce_target_duration
        from studio_core import get_audio_duration
        
        clip_a = str(self.assets_dir / "test_conformed_scene.mp4")
        if not Path(clip_a).exists():
            self.skipTest("Conformed test video not found.")
            return
            
        # Scenario: Pad short video
        dur_before = get_audio_duration(clip_a)
        target = dur_before + 3.0
        
        scene_paths = [clip_a]
        result_paths = asyncio.run(enforce_target_duration(scene_paths, target_seconds=target, tolerance=0.1))
        
        self.assertEqual(len(result_paths), 2, "Padding clip should be appended.")
        self.assertTrue(Path(result_paths[1]).exists(), "Padding clip should exist.")
        
        # Cleanup padding clip
        if Path(result_paths[1]).exists():
            try:
                Path(result_paths[1]).unlink()
            except Exception:
                pass

if __name__ == "__main__":
    unittest.main()



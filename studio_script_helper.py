import os
# Thread safety
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import sys
import json
import argparse
from pathlib import Path
from studio_core import generate_hindi_script, ingest_performance

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["generate", "ingest"], required=True)
    parser.add_argument("--topic")
    parser.add_argument("--output")
    parser.add_argument("--duration", type=int, default=4)
    parser.add_argument("--language", default="hi", help="Target language for script (hi, en, es)")
    parser.add_argument("--video-id")
    parser.add_argument("--script-text")
    parser.add_argument("--score", type=int)
    args = parser.parse_args()
    
    if args.action == "generate":
        if not args.topic or not args.output:
            print("Error: --topic and --output are required for generate action.", file=sys.stderr)
            sys.exit(1)
            
        script = generate_hindi_script(args.topic, args.duration)
        
        # Translate script if language is not Hindi
        if args.language and args.language.lower() != "hi":
            print(f"[Script Helper] Translating script to {args.language}...")
            from studio_core import localize_script
            for scene in script:
                try:
                    translated_narration = localize_script(scene["narration"], args.language)
                    scene["narration"] = translated_narration
                    scene["language"] = args.language.lower()
                except Exception as e:
                    print(f"[WARNING] Translation failed for scene: {e}. Keeping original.")
                    scene["language"] = "hi"
                    
        from pathlib import Path
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2)
        print(f"Script successfully generated and saved to {args.output}")
        
    elif args.action == "ingest":
        if not args.video_id or not args.script_text or args.score is None:
            print("Error: --video-id, --script-text, and --score are required for ingest action.", file=sys.stderr)
            sys.exit(1)
            
        # RAG Ingestion
        ingest_performance(args.video_id, args.script_text, args.score)
        
        # Bandit Ingestion
        manifest_file = Path.cwd() / "assets" / f"render_manifest_{args.video_id}.json"
        if not manifest_file.exists():
            manifest_file = Path.cwd() / "assets" / "render_manifest.json"
            
        selected_hook = None
        if manifest_file.exists():
            try:
                with open(manifest_file, "r") as mf:
                    m_data = json.load(mf)
                    selected_hook = m_data.get("selected_hook")
            except Exception:
                pass
                
        if selected_hook:
            reward = float(args.score) / 100.0
            from studio_core import update_bandit_arm
            update_bandit_arm(selected_hook, reward)
            print(f"Updated bandit arm '{selected_hook}' with reward {reward:.2f}")

if __name__ == "__main__":
    main()

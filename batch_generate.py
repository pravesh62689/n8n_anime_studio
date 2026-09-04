# batch_generate.py
import subprocess
import sys
import time

TOPICS = [
    ("magical forest adventure and friendship", "FINAL_MASTERPIECE_1.mp4"),
    ("clever little monkey and the hungry crocodile", "FINAL_MASTERPIECE_2.mp4"),
    ("adventures of a tiny seed growing into a giant tree", "FINAL_MASTERPIECE_3.mp4"),
    ("the brave little fire engine that saved the day", "FINAL_MASTERPIECE_4.mp4"),
    ("cute puppy discovering the secrets of the garden", "FINAL_MASTERPIECE_5.mp4")
]

def main():
    print(f"=== Starting Batch Production of {len(TOPICS)} Animated Videos ===")
    
    for idx, (topic, output_name) in enumerate(TOPICS, start=1):
        print(f"\n==================================================")
        print(f"PRODUCING VIDEO {idx}/{len(TOPICS)}")
        print(f"Topic: '{topic}'")
        print(f"Output File: '{output_name}'")
        print(f"==================================================")
        
        cmd = [
            ".venv\\Scripts\\python.exe", "-u", "orchestrator.py",
            "--topic", topic,
            "--output", output_name
        ]
        
        start_time = time.time()
        try:
            # Execute orchestrator run
            res = subprocess.run(cmd, check=True)
            elapsed = time.time() - start_time
            print(f"SUCCESS: Video {idx} ('{output_name}') compiled in {elapsed:.2f} seconds.")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Video {idx} generation failed with return code {e.returncode}")
            # Continue to next video if one fails
            continue
            
    print("\n=== Batch Production Complete! All requested videos processed. ===")

if __name__ == "__main__":
    main()

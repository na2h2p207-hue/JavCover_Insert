#!/usr/bin/env python
"""
Simple faststart script - uses FFmpeg to move moov atom to beginning.
Usage:
    python faststart.py "filename.mp4"
    python faststart.py                 # Process all MP4 in parent dir
"""

import os
import sys
import subprocess
import shutil
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def faststart(video_path):
    """Run FFmpeg faststart on a single file."""
    print(f"\nProcessing: {os.path.basename(video_path)}")
    
    if not os.path.exists(video_path):
        print(f"  [Error] File not found")
        return False
    
    temp_path = video_path + ".temp.mp4"
    
    try:
        # Run FFmpeg
        print(f"  [FFmpeg] Running faststart...")
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
                "-i", video_path,
                "-c", "copy",
                "-movflags", "+faststart",
                temp_path
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.stderr:
            print(f"  [FFmpeg] {result.stderr.strip()}")
        
        if result.returncode != 0:
            print(f"  [Error] FFmpeg failed")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
        
        # Check temp file
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            print(f"  [Error] Temp file empty or missing")
            return False
        
        # Replace original with temp
        print(f"  [Replace] Swapping files...")
        time.sleep(1)  # Let Windows release any handles
        
        # Try multiple times in case of file lock
        for attempt in range(5):
            try:
                os.remove(video_path)
                shutil.move(temp_path, video_path)
                print(f"  [Success] Done!")
                return True
            except PermissionError:
                print(f"  [Wait] File locked, retrying in {(attempt+1)*2}s...")
                time.sleep((attempt+1) * 2)
        
        print(f"  [Error] Could not replace file (locked)")
        print(f"  [Info] Temp file saved as: {temp_path}")
        return False
        
    except FileNotFoundError:
        print("  [Error] FFmpeg not found! Install FFmpeg first.")
        return False
    except Exception as e:
        print(f"  [Error] {e}")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False


def main():
    if len(sys.argv) > 1:
        # Process specific file
        target = sys.argv[1]
        if not os.path.isabs(target):
            # Check in parent directory first
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target = os.path.join(parent_dir, target)
        faststart(target)
    else:
        # Process all MP4 in parent directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"Scanning: {parent_dir}")
        
        for filename in sorted(os.listdir(parent_dir)):
            if filename.lower().endswith(".mp4"):
                faststart(os.path.join(parent_dir, filename))


if __name__ == "__main__":
    main()

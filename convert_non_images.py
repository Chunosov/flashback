import argparse
import os
import subprocess
import sys
from pathlib import Path

# Common video file extensions
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}

def is_video_file(path):
    """Check if the given path is a video file based on extension."""
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS

def process_file(file_path, base_frames_dir, upscale=False):
    """Process a single file, converting to frames if it's a video."""
    if not is_video_file(file_path):
        print(f"Skipping non-video file: {file_path}")
        return
    
    if not os.path.exists(file_path):
        print(f"Warning: File does not exist: {file_path}")
        return
    
    # Get parent directory name for output subdir
    parent_dir = Path(file_path).parent.name
    output_dir = os.path.join(base_frames_dir, parent_dir)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Converting video: {file_path}")
    print(f"Output directory: {output_dir}")
    
    try:
        # Call video_to_frames.py
        cmd = [
            sys.executable,
            'video_to_frames.py',
            file_path,
            '-o', output_dir
        ]
        
        # Add upscale flag if enabled
        if upscale:
            cmd.append('--upscale')
        
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error processing video {file_path}: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='Convert non-image files (videos) to frames')
    parser.add_argument('input_file', nargs='?', default='non_photos.txt',
                       help='Input file containing paths (default: non_photos.txt)')
    parser.add_argument('-o', '--output-dir', required=True,
                       help='Base directory for output frames')
    parser.add_argument('-u', '--upscale', action='store_true',
                       help='Upscale frames that are below FullHD (1920x1080) resolution')
    
    args = parser.parse_args()
    
    # Ensure input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    # Process each line in the input file
    with open(args.input_file, 'r') as f:
        for line in f:
            file_path = line.strip()
            if file_path:  # Skip empty lines
                process_file(file_path, args.output_dir, args.upscale)

if __name__ == "__main__":
    main()

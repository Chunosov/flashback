import cv2
import os
import sys
import argparse
from pathlib import Path
from upscale import upscale_image

def is_below_fullhd(image):
    """
    Check if image resolution is below FullHD (1920x1080).
    
    Args:
        image: OpenCV image array
        
    Returns:
        bool: True if image is below FullHD resolution
    """
    height, width = image.shape[:2]
    return width < 1920 or height < 1080

def extract_frames(video_path, interval=10, output_dir=None, upscale=False):
    """
    Extract frames from a video file at specified intervals.
    
    Args:
        video_path (str): Path to the video file
        interval (int): Interval in seconds between frames (default: 10)
        output_dir (str): Directory to save frames (default: based on video filename)
    """
    # Open the video file
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    # Get video properties
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    
    # Calculate frame interval
    frame_interval = int(fps * interval)
    
    # Create output directory
    if output_dir is None:
        video_name = Path(video_path).stem
        output_dir = f"{video_name}_frames"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Process video
    current_frame = 0
    frames_saved = 0
    
    print(f"Video duration: {duration:.2f} seconds")
    print(f"Extracting frames every {interval} seconds...")
    
    while True:
        # Set frame position
        video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        
        # Read frame
        ret, frame = video.read()
        if not ret:
            break
        
        # Calculate timestamp
        timestamp = current_frame / fps
        
        # Generate output filename
        output_file = os.path.join(output_dir, f"{Path(video_path).stem}_{int(timestamp)}s.jpg")
        
        # Check if upscaling is needed
        if upscale and is_below_fullhd(frame):
            # Save original frame temporarily
            temp_file = output_file.replace('.jpg', '_temp.jpg')
            cv2.imwrite(temp_file, frame)
            
            # Upscale the frame
            try:
                upscale_image(temp_file, output_file)
                os.remove(temp_file)  # Clean up temp file
                print(f"Saved and upscaled frame at {int(timestamp)}s -> {output_file}")
            except Exception as e:
                print(f"Warning: Failed to upscale frame at {int(timestamp)}s: {e}")
                # If upscaling fails, save original frame
                os.rename(temp_file, output_file)
                print(f"Saved original frame at {int(timestamp)}s -> {output_file}")
        else:
            # Save frame without upscaling
            cv2.imwrite(output_file, frame)
            print(f"Saved frame at {int(timestamp)}s -> {output_file}")
        
        frames_saved += 1
        
        # Move to next interval
        current_frame += frame_interval
        if current_frame >= frame_count:
            break
    
    video.release()
    print(f"\nCompleted! Saved {frames_saved} frames to {output_dir}/")
    return frames_saved

def main():
    parser = argparse.ArgumentParser(description='Extract frames from a video file at specified intervals')
    parser.add_argument('video_path', help='Path to the video file')
    parser.add_argument('-i', '--interval', type=int, default=10,
                       help='Interval between frames in seconds (default: 10)')
    parser.add_argument('-o', '--output-dir', help='Output directory (default: based on video filename)')
    parser.add_argument('-u', '--upscale', action='store_true',
                       help='Upscale frames that are below FullHD (1920x1080) resolution')
    
    args = parser.parse_args()
    
    try:
        # Verify video file exists
        if not os.path.exists(args.video_path):
            print(f"Error: Video file not found: {args.video_path}", file=sys.stderr)
            sys.exit(1)
        
        # Extract frames
        extract_frames(args.video_path, args.interval, args.output_dir, args.upscale)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

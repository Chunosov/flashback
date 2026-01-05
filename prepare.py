import os
import sys
import argparse

# Configure how often to report progress and save files
PROGRESS_INTERVAL = 100

# Common media file extensions (excluding jpg/jpeg)
MEDIA_EXTENSIONS = {
    # Images
    '.png', '.gif', '.bmp', '.tiff', '.webp', '.psd', '.ai', '.raw', '.cr2', '.nef',
    # Videos
    '.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm', '.m4v', '.mpg', '.mpeg'
}

def has_jpg_counterpart(file_path):
    """Check if there's a jpg version of the file in the same directory."""
    dirname = os.path.dirname(file_path)
    filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # Get list of all files in directory
    dir_files = os.listdir(dirname)
    
    # Convert filename to lowercase for case-insensitive comparison
    filename_lower = filename.lower()
    
    # Check for any jpg/jpeg file that matches our filename (case-insensitive)
    for file in dir_files:
        name, ext = os.path.splitext(file)
        if (name.lower() == filename_lower and 
            ext.lower() in ('.jpg', '.jpeg')):
            return True
    
    return False

def find_media_files(root_dir, photos_file='photos.txt', non_photos_file=None):
    """Find both JPG files and non-JPG media files without JPG counterparts."""
    jpg_files = []
    non_jpg_files = []
    files_processed = 0
    
    # Walk through directory recursively
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            # Get file extension in lowercase
            ext = os.path.splitext(filename)[1].lower()
            absolute_path = os.path.abspath(os.path.join(dirpath, filename))
            
            if ext in ('.jpg', '.jpeg'):
                # Add JPG files to photos list
                jpg_files.append(absolute_path)
            elif ext in MEDIA_EXTENSIONS and non_photos_file:
                # For non-JPG media files, check if they have JPG counterparts
                # Only process if non_photos_file is specified
                if not has_jpg_counterpart(absolute_path):
                    non_jpg_files.append(absolute_path)
            
            files_processed += 1
            if files_processed % PROGRESS_INTERVAL == 0:
                print(f"Processed {files_processed} files...")
                # Save intermediate results
                save_results(jpg_files, photos_file)
                if non_photos_file:
                    save_results(non_jpg_files, non_photos_file)
    
    return jpg_files, non_jpg_files

def save_results(file_list, target_file):
    """Save the list of files to the target file."""
    with open(target_file, "w") as f:
        for file_path in file_list:
            f.write(file_path + "\n")

def main():
    parser = argparse.ArgumentParser(
        description='Find both JPG files and non-JPG media files in a directory tree.'
    )
    parser.add_argument('root_path', help='Root directory to scan for media files')
    parser.add_argument('output_file', nargs='?', default='photos.txt',
                       help='Target file to save JPG files list (default: photos.txt)')
    parser.add_argument('--non-photos',
                       help='Optional: Target file to save non-JPG media files list')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.root_path):
        print(f"Error: Root path '{args.root_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(args.root_path):
        print(f"Error: '{args.root_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Find all media files
    jpg_files, non_jpg_files = find_media_files(args.root_path, args.output_file, args.non_photos)
    
    # Save final results
    save_results(jpg_files, args.output_file)
    if args.non_photos:
        save_results(non_jpg_files, args.non_photos)
    
    print(f"\nCompleted!")
    print(f"Total JPG files found: {len(jpg_files)}")
    if args.non_photos:
        print(f"Total non-JPG media files found: {len(non_jpg_files)}")
        print(f"Non-JPG media files saved to: {args.non_photos}")
    print(f"JPG files saved to: {args.output_file}")

if __name__ == "__main__":
    main()

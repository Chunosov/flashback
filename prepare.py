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

def process_directory(directory, jpg_files, non_jpg_files, non_photos_file=None):
    """Process a single directory and update the file lists."""
    files_processed = 0
    
    # Walk through directory recursively
    for dirpath, dirnames, filenames in os.walk(directory):
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
                print(f"Processed {files_processed} files in {directory}...")
    
    print(f"Total processed {files_processed} files in {directory}...")
    return files_processed

def find_media_files(root_path, photos_file='photos.txt', non_photos_file=None):
    """Find both JPG files and non-JPG media files without JPG counterparts."""
    jpg_files = []
    non_jpg_files = []
    total_files_processed = 0
    
    if os.path.isfile(root_path):
        # If root_path is a file, read directories from it
        with open(root_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                    
                if os.path.exists(line) and os.path.isdir(line):
                    print(f"\nProcessing directory: {line}")
                    files_processed = process_directory(line, jpg_files, non_jpg_files, non_photos_file)
                    total_files_processed += files_processed
                else:
                    print(f"Warning: '{line}' is not a valid directory, skipping", file=sys.stderr)
    else:
        # Process single directory
        print(f"\nProcessing directory: {root_path}")
        total_files_processed = process_directory(root_path, jpg_files, non_jpg_files, non_photos_file)
    
    return jpg_files, non_jpg_files, total_files_processed

def save_results(file_list, target_file):
    """Save the list of files to the target file."""
    with open(target_file, "w") as f:
        for file_path in file_list:
            f.write(file_path + "\n")

def main():
    parser = argparse.ArgumentParser(
        description='Find both JPG files and non-JPG media files in a directory tree.'
    )
    parser.add_argument('root_path', help='Directory to scan for media files, or a file containing a list of directories (one per line, # for comments)')
    parser.add_argument('output_file', nargs='?', default='photos.txt',
                       help='Target file to save JPG files list (default: photos.txt)')
    parser.add_argument('--non-photos',
                       help='Optional: Target file to save non-JPG media files list')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.root_path):
        print(f"Error: Path '{args.root_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Find all media files
    jpg_files, non_jpg_files, total_processed = find_media_files(args.root_path, args.output_file, args.non_photos)
    
    # Save final results
    save_results(jpg_files, args.output_file)
    if args.non_photos:
        save_results(non_jpg_files, args.non_photos)
    
    print(f"\nCompleted! Total files processed: {total_processed}")
    print(f"Total JPG files found: {len(jpg_files)}")
    if args.non_photos:
        print(f"Total non-JPG media files found: {len(non_jpg_files)}")
        print(f"Non-JPG media files saved to: {args.non_photos}")
    print(f"JPG files saved to: {args.output_file}")

if __name__ == "__main__":
    main()

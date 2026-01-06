# Flashback

Take a shot. Take a shot. Repeat for tens of years. Point 

## Requirements

Install Python dependencies using:

```bash
pip install -r requirements.txt
```

On Linux (Ubuntu/Debian), install required system libraries:

```bash
sudo apt-get install libomp5
```

On other systems:
- macOS: `brew install libomp`
- Windows: No additional setup needed (included with binary wheels)

## Main features

### Image listing

Prepare a list of files that will be displayed in slideshow:

```bash
# Basic usage (outputs to photos.txt and photos-non.txt)
python prepare.py "/path/to/directory"

# Specify custom output files
python prepare.py "/path/to/directory" --photos my_photos.txt --non-photos my_non_photos.txt

# Example with photo album directory
python prepare.py "/media/nikolay/Album/Photo/Фотоальбомы/Фотоальбом 1/"
```

The script will:
1. Recursively scan the directory for media files
2. Save JPG files to `photos.txt` (or specified output)
3. Save non-JPG media files (without JPG counterparts) to `photos-non.txt` (or specified output)

### Slideshow

Display images from a prepared list file in a slideshow:

```bash
# Basic usage (reads from photos.txt)
python slideshow.py

# Use custom image list file
python slideshow.py my_photos.txt

# Remote slideshow mode (fetch images from server)
python slideshow.py my_album --server http://example.com
```

Server Mode:
When using the `--server` option, the slideshow operates in remote mode:
1. The image list file name is used as a key to identify the slideshow on the server
2. Images are fetched on-demand from the server API

Server API Endpoints:
- `GET /api/slideshow/{key}/list`
  - Returns a JSON array of image paths for the slideshow
  - Example response: `["photos/2023/img1.jpg", "photos/2023/img2.jpg"]`
- `GET /api/slideshow/{key}/image/{image_id}`
  - Returns the binary image data
  - image_id is the base64-encoded full image path
  - Returns appropriate content-type header for the image

Features:
- Automatic image progression with configurable interval
- Smart image preloading and caching for smooth transitions
- EXIF orientation support for correct image display
- Automatic logging of corrupted/unreadable images
- Hover-activated UI elements:
  - Top toolbar: Previous, Play/Pause, Fullscreen, Settings
  - Bottom-right: File name and path display
  - Top-right: Parent directory and photo year display

Controls:
- F11: Toggle fullscreen mode
- ESC: Exit slideshow
- Mouse hover top edge: Show control toolbar
- Mouse hover bottom-right: Show file details
- Settings dialog: Configure slideshow interval (1-60 seconds)

Configuration:
- Settings are automatically saved to `config.ini`
- Saved preferences include:
  - Slideshow interval
  - Window size
  - Fullscreen state

### Slideshow Server

The project includes a Flask server that can serve slideshows remotely. This allows running the slideshow on one machine while serving images from another.

```bash
# Basic usage (serve a single slideshow)
python slideshow_server.py photos.txt

# Serve multiple slideshows
python slideshow_server.py album1.txt album2.txt vacation.txt

# Specify host and port
python slideshow_server.py --host 0.0.0.0 --port 8080 photos.txt

# Run in debug mode
python slideshow_server.py --debug photos.txt
```

Server Features:
- Serve multiple slideshows simultaneously
- Each slideshow is identified by its file name (without extension)
- Secure path handling to prevent directory traversal
- Automatic content-type detection for images
- Error handling with appropriate HTTP status codes

Example Usage:
1. Start the server:
   ```bash
   python slideshow_server.py --host 0.0.0.0 --port 8080 my_photos.txt
   ```

2. Run the slideshow client:
   ```bash
   python slideshow.py my_photos --server http://server:8080
   ```

The server will use the image list file's parent directory as the base directory for serving images, ensuring that only files within that directory tree can be accessed.

## Additional features

### Image Upscaling
The project includes a wrapper for Real-ESRGAN image upscaling, supporting:
- Single image upscaling
- Batch directory processing
- Multiple pre-trained models:
  - realesrgan-x4plus (default, good for general images)
  - realesrnet-x4plus (sharper but may have more artifacts)
  - realesrgan-x4plus-anime (optimized for anime/art)

Example usage:
```bash
# Upscale a single image
python upscale.py input.jpg -o output.jpg

# Upscale with different model
python upscale.py input.jpg -m realesrgan-x4plus-anime

# Process entire directory
python upscale.py input_directory -o output_directory

# Specify scale factor (2x, 3x, or 4x)
python upscale.py input.jpg -s 2
```

### Video Frame Extraction
Extract frames from video files at specified intervals. Optionally upscale frames that are below FullHD (1920x1080) resolution:

```bash
# Basic frame extraction
python video_to_frames.py video.mp4 -o frames_directory

# Extract frames every 5 seconds
python video_to_frames.py video.mp4 -i 5

# Extract frames and upscale those below FullHD
python video_to_frames.py video.mp4 --upscale

# Combine options: extract every 5 seconds and upscale if needed
python video_to_frames.py video.mp4 -i 5 --upscale -o frames_directory
```

### Batch Video Processing
Convert multiple video files to frames using a list file (supports .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm):

```bash
# Process videos listed in non_photos.txt (default input file)
python convert_non_images.py -o all_frames

# Process videos from a custom list file
python convert_non_images.py custom_list.txt -o frames_output

# Enable upscaling for frames below FullHD resolution
python convert_non_images.py -o all_frames --upscale

# Process custom list with upscaling
python convert_non_images.py custom_list.txt -o frames_output -u

# The script will:
# 1. Read video paths from the input file
# 2. Create subdirectories in the output directory matching source video locations
# 3. Extract frames from each video using video_to_frames.py
```

## Project Structure
- `upscale.py` - Real-ESRGAN image upscaling wrapper
- `video_to_frames.py` - Video frame extraction utility
- `convert_non_images.py` - Convert non-image files to frames
- `prepare.py` - Media file discovery utility (finds both photos and non-photo media files)
- `slideshow.py` - Image slideshow functionality
- `slideshow_server.py` - Flask server for remote slideshow functionality

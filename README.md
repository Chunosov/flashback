# Flashback

Take a shot. Take a shot. Repeat for tens of years. Point 

## Requirements

Install Python dependencies using:

```bash
# All dependicies are required only for video and image preprocessing
pip install -r requirements.txt

# Install only part of dependencies required for running slideshow server
pip install -r requirements_server.txt

# Install only part of dependencies required 
# for running prepared slideshow (either localy or via server)
pip install -r requirements_client.txt
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
# Basic usage (outputs to photos.lst)
python prepare.py "/path/to/directory"

# Specify custom output files
# Unless specified, the ".lst" extension is added automatically 
python prepare.py "/path/to/directory" my_photos --non-photos my_non_photos

# Specify several input dirs via input file
# Input file should contain one directory per line,
# use # at the line start to skip particular directories
python prepare.py new_year_dirs.lst new_year
```

The script will:
1. Recursively scan the directory for media files
2. Save JPG file paths to `photos.lst` (or specified output)
3. Optionally save non-JPG media file paths (without JPG counterparts) to specified output

### Slideshow

Display images from a prepared list file in a slideshow:

```bash
# Basic usage (reads from photos.lst)
python slideshow.py

# Use custom image list file
python slideshow.py my_photos.lst

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
- `F11`: Toggle fullscreen mode
- `ESC`: Exit slideshow
- `Space`: Pasue/Resume slideshow
- `Backspace`: Show the previous image
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
# Basic usage
python server.py

# Run server on a dedicated port
python server.py --port 8080

# Run in debug mode
python server.py --debug

# Run the slideshow client
python slideshow.py my_photos --server http://192.168.1.98:8080
```

Server Features:
- Serve multiple slideshows simultaneously
- Each slideshow is identified by its file name (without extension)
- Automatic content-type detection for images
- Error handling with appropriate HTTP status codes

## Image preprocessing

Install all dependencies to do image preprocessing:

```bash
pip install -r requirements.txt
```

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
# Process videos listed in non_photos.lst (default input file)
python convert_non_images.py -o all_frames

# Process videos from a custom list file
python convert_non_images.py custom_list.lst -o frames_output

# Enable upscaling for frames below FullHD resolution
python convert_non_images.py -o all_frames --upscale

# Process custom list with upscaling
python convert_non_images.py custom_list.lst -o frames_output -u
```

The script will:
1. Read video paths from the input file
2. Create subdirectories in the output directory matching source video locations
3. Extract frames from each video using `video_to_frames.py`

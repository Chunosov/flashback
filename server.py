from flask import Flask, jsonify, send_file, abort
import os
import mimetypes
import argparse

app = Flask(__name__)

# Store slideshow configurations
slideshows = {}

@app.route('/api/slideshow/<key>/list')
def get_image_list(key):
    """Load and return the list of images for a slideshow"""
    if key not in slideshows:
        try:
            photos_file = key
            if not photos_file.endswith('.txt'):
                photos_file = key + '.txt'
            if not os.path.exists(photos_file):
                abort(404, description=f"Slideshow '{key}' not found")
            with open(photos_file, 'r') as f:
                paths = f.read().splitlines()
                slideshows[key] = paths
                print(f"Slideshow '{key}' loaded, image paths: {len(paths)}")
        except Exception as e:
            print(f"Error loading image list '{photos_file}': {e}")
            abort(500, description=f"Error loading image list for slideshow '{key}': {e}")
    return jsonify(slideshows[key])

@app.route('/api/slideshow/<key>/image/<image_index>')
def get_image(key, image_index):
    """Return an image file content by index"""
    if key not in slideshows:
        abort(404, description=f"Slideshow '{key}' not found")
    try:
        image_paths = slideshows[key]
        image_index = int(image_index)
        if image_index < 0 or image_index >= len(image_paths):
            abort(404, description=f"Image not found: {image_index}")
        image_path = image_paths[image_index]
        if not os.path.isfile(image_path):
            print(f"Image not found: {image_path}")
            abort(404, description=f"Image not found: {image_index}")
        
        # Determine content type
        content_type = mimetypes.guess_type(image_path)[0]
        if not content_type or not content_type.startswith('image/'):
            abort(400, description=f"Invalid image file: {image_path}")
        
        return send_file(image_path, mimetype=content_type)
    
    except Exception as e:
        print(f"Error loading image {image_index} for slideshow '{key}': {e}")
        abort(500, description=str(e))

def main():
    parser = argparse.ArgumentParser(description='Slideshow server')
    parser.add_argument('--host', default='0.0.0.0',
                      help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                      help='Port to listen on (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                      help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Run the server
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()

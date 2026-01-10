import tkinter as tk
from PIL import Image, ImageTk, ExifTags
import random
import configparser
import os
from datetime import datetime
import threading
from queue import Queue
import argparse
import requests
import base64
from io import BytesIO

from utils import ensure_ext, DEF_EXT

FILENAME_PANEL_HEIGHT = 150
FILENAME_PANEL_MARGIN = 20
FILENAME_PANEL_PADDING = 15
TOOLBAR_WIDTH = 700
TOOLBAR_HEIGHT = 80
TOOLBAR_MARGIN = 20
CONFIG_FILE = 'config.ini'
CONFIG_DLG_WIDTH = 400
CONFIG_DLG_HEIGHT = 300
DIRNAME_PANEL_MARGIN = 20
DIRNAME_PANEL_PADDING = 15
DIRNAME_PANEL_HEIGHT = 60
MAX_ERROR_COUNT = 5

class Slideshow:
    def __init__(self, root, photos_file, server_url):
        self.is_paused = False
        self.is_fullscreen = False
        self.photos_file = photos_file
        self.server_url = server_url
        self.error_count = 0
        self.current_year = None
        
        # Image cache dictionary
        self.image_cache = {}
        self.cache_size = 5  # Keep last N images in cache
        
        # Queue for background loading
        self.load_queue = Queue()
        self.loading_thread = threading.Thread(target=self.background_loader, daemon=True)
        self.loading_thread.start()
        
        # Store start timestamp for bad images log
        self.start_timestamp = datetime.now()
        self.bad_images_file = None

        self.root = root
        self.root.title("Photo Slideshow")
        
        # Load settings before configuring window
        self.config = configparser.ConfigParser()
        self.load_settings()
        
        # Apply loaded window state
        self.root.attributes('-fullscreen', self.is_fullscreen)
        if not self.is_fullscreen:
            # Center the window on screen
            x = (self.root.winfo_screenwidth() - self.window_size[0]) // 2
            y = (self.root.winfo_screenheight() - self.window_size[1]) // 2
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{x}+{y}")
        
        # Set black background
        self.root.configure(bg='black')
        
        # Bind Escape key to exit
        self.root.bind('<Escape>', lambda e: self.root.quit())
        # Bind F11 key to toggle fullscreen
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        # Bind Backspace key to previous image
        self.root.bind('<BackSpace>', lambda e: self.show_previous_image())
        # Bind Space key to toggle pause
        self.root.bind('<space>', lambda e: self.toggle_pause())

        # Create main frame for images
        self.main_frame = tk.Frame(root, bg='black')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create label for displaying images with black background
        self.label = tk.Label(self.main_frame, bg='black')
        self.label.pack(fill=tk.BOTH, expand=True)
        
        # Create a toplevel window for the buttons
        self.button_window = tk.Toplevel(root)
        self.button_window.overrideredirect(True)  # Remove window decorations
        self.button_window.attributes('-topmost', True)  # Keep on top
        self.button_window.configure(bg='black')
        
        # Create button frame to hold both buttons
        self.button_frame = tk.Frame(self.button_window, bg='black')
        self.button_frame.pack(expand=True, fill=tk.BOTH)
        
        # Create tool buttons
        self.prev_button = self.create_toolbutton("⬅ Prev", self.show_previous_image)
        self.pause_button = self.create_toolbutton("⏸️ Pause", self.toggle_pause)
        self.fullscreen_button = self.create_toolbutton("🔲", self.toggle_fullscreen)
        self.settings_button = self.create_toolbutton("⚙️", self.show_settings)
        
        # Initially hide the button window
        self.button_window.withdraw()
        
        # Bind mouse motion and window resize
        self.root.bind('<Motion>', self.check_mouse_position)
        self.root.bind('<Configure>', self.on_window_configure)
        
        # Create a toplevel window for the filename label
        self.label_window = tk.Toplevel(root)
        self.label_window.overrideredirect(True)  # Remove window decorations
        self.label_window.attributes('-topmost', True)  # Keep on top
        self.label_window.configure(bg='gray20')
        
        # Create frame for labels with right alignment
        label_frame = tk.Frame(self.label_window, bg='gray20', padx=FILENAME_PANEL_PADDING, pady=15)
        label_frame.pack(anchor='e')  # Align frame to the right
        
        # Create filename label (just the name)
        self.filename_label = tk.Label(label_frame, 
                                     bg='gray20', fg='white',
                                     font=('Arial', 20, 'bold'),
                                     justify=tk.RIGHT,
                                     anchor='e')  # Right-align text
        self.filename_label.pack(anchor='e')  # Align label to the right
        
        # Create path label (full path)
        self.path_label = tk.Label(label_frame,
                                 bg='gray20', fg='white',
                                 font=('Arial', 12),
                                 justify=tk.RIGHT,
                                 anchor='e')  # Right-align text
        self.path_label.pack(anchor='e')  # Align label to the right
        
        # Add border around the frame
        #label_frame.configure(bd=1, relief='solid')
        self.label_window.configure(bd=1, relief='solid')
        
        # Initially hide the label window
        self.label_window.withdraw()
        
        # Create a toplevel window for the parent directory label
        self.parent_dir_window = tk.Toplevel(root)
        self.parent_dir_window.overrideredirect(True)  # Remove window decorations
        self.parent_dir_window.attributes('-topmost', True)  # Keep on top
        self.parent_dir_window.attributes('-alpha', 1.0)  # Make fully visible
        self.parent_dir_window.configure(bg='black')  # Set black background
        
        # Create parent directory label
        self.parent_dir_label = tk.Label(self.parent_dir_window,
                                       bg='black',
                                       fg='white',
                                       font=('Arial', 20, 'bold'))
        self.parent_dir_label.pack(anchor='e', padx=20)
        
        # Track if UI elements are visible
        self.button_visible = False
        self.label_visible = False
        
        # Load image paths
        self.load_file_list()
        self.current_index = 0
        
        # Start the slideshow
        self.show_current_image()
        # Start automatic progression
        self.timer_id = self.root.after(self.interval, self.show_next_image)

    def load_file_list(self):
        image_paths = []
        self.image_paths = []
        print(f"Loading image paths from {self.photos_file}...")
        if self.server_url:
            try:
                response = requests.get(f"{self.server_url}/api/slideshow/{self.photos_file}/list")
                if response.ok:
                    image_paths = response.json()
                else:
                    raise Exception(f"Failed to get image list from server: {response.status_code}")
            except Exception as e:
                raise Exception(f"Failed to connect to server: {e}")
        else:
            with open(self.photos_file, 'r') as f:
                image_paths = f.read().splitlines()

        # Randomize images and store paths in the same random order
        # In remote mode images are loaded by indexes but 
        # paths are still required to display image name
        
        self.image_indexes = [*range(len(image_paths))]
        random.shuffle(self.image_indexes)
        for index in self.image_indexes:
            self.image_paths.append(image_paths[index])
        print(f"Loaded image paths: {len(self.image_paths)}")

    def create_toolbutton(self, text, command):
        button = tk.Button(self.button_frame, text=text, command=command,
                            bg='black', fg='white',
                            activebackground='gray25',
                            activeforeground='white',
                            bd=1,  # Thicker border
                            relief='solid',  # Solid border style
                            padx=10, pady=10,  # Add padding
                            font=('Arial', 16, 'bold'))  # Larger, bold font
        button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
        return button

    def check_mouse_position(self, event):
        # Get window dimensions
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Show button window if mouse is in upper-right corner
        if event.x < TOOLBAR_WIDTH + TOOLBAR_MARGIN and \
           event.y < TOOLBAR_HEIGHT + TOOLBAR_MARGIN:

            # Position window relative to main window
            root_x = self.root.winfo_x()
            root_y = self.root.winfo_y()

            pos_x = root_x + TOOLBAR_MARGIN
            pos_y = root_y + TOOLBAR_MARGIN
            if not self.button_visible:
                self.button_window.geometry(f'{TOOLBAR_WIDTH}x{TOOLBAR_HEIGHT}+{pos_x}+{pos_y}')
                self.button_window.lift()  # Ensure it's on top
                self.button_window.deiconify()
                self.button_visible = True
        else:
            if self.button_visible:
                self.button_window.withdraw()
                self.button_visible = False
        
        # Show filename if mouse is in bottom-right corner
        if event.x > window_width - 1000 and \
            event.y > window_height - FILENAME_PANEL_HEIGHT - FILENAME_PANEL_MARGIN:
            if not self.label_visible:
                # Get current file path and name
                current_path = self.image_paths[self.current_index]
                #current_file = os.path.basename(os.path.dirname(current_path))
                current_file = os.path.basename(current_path)
                
                # Update labels
                self.filename_label.configure(text=current_file)
                self.path_label.configure(text=current_path)
                
                # Calculate required width for the text
                self.label_window.update_idletasks()  # Ensure sizes are updated
                required_width = max(
                    self.filename_label.winfo_reqwidth(),
                    self.path_label.winfo_reqwidth()
                ) + FILENAME_PANEL_PADDING * 2
                
                # Position window relative to main window
                root_x = self.root.winfo_x()
                root_y = self.root.winfo_y()
                
                if self.is_fullscreen:
                    # In fullscreen mode, position relative to screen edge
                    x_pos = window_width - required_width - FILENAME_PANEL_MARGIN
                    y_pos = window_height - FILENAME_PANEL_HEIGHT - FILENAME_PANEL_MARGIN
                else:
                    # In windowed mode, position relative to window
                    x_pos = root_x + window_width - required_width - FILENAME_PANEL_MARGIN
                    y_pos = root_y + window_height - FILENAME_PANEL_HEIGHT - FILENAME_PANEL_MARGIN
                
                self.label_window.geometry( \
                    f'{required_width}x{FILENAME_PANEL_HEIGHT}+{x_pos}+{y_pos}')
                self.label_window.lift()  # Ensure it's on top
                self.label_window.deiconify()
                self.label_visible = True
        else:
            if self.label_visible:
                self.label_window.withdraw()
                self.label_visible = False
    
    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def load_image_sync(self, index):
        """Load image synchronously and return it"""
        try:
            if self.server_url:
                origin_index = self.image_indexes[index]
                url = f"{self.server_url}/api/slideshow/{self.photos_file}/image/{origin_index}"
                try:
                    response = requests.get(url, timeout=10)  # 10 second timeout
                    if response.ok:
                        image = Image.open(BytesIO(response.content))
                    else:
                        raise Exception(f"Server returned status code: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    raise Exception(f"Network error: {e}")
            else:
                image = Image.open(self.image_paths[index])
            
            image = self.apply_exif_orientation(image)
            self.current_year = self.extract_year_from_exif(image)
            self.image_cache[index] = image
            self.error_count = 0
            return image
        except Exception as e:
            print(f"Error loading image {self.image_paths[index]}: {e}")
            self.error_count += 1
            if self.error_count == MAX_ERROR_COUNT:
                print("Too many errors, exiting")
                exit(1)
            return None

    def show_previous_image(self):
        # Go to previous image
        self.stop_timer()

        prev_index = (self.current_index - 2) % len(self.image_paths)
        
        # If image is not in cache, load it synchronously
        if prev_index not in self.image_cache:
            image = self.load_image_sync(prev_index)
            if image is None:
                # Skip to next if loading failed
                self.current_index = (prev_index + 1) % len(self.image_paths)
                self.show_next_image()
                return
                
        self.current_index = prev_index
        self.show_next_image()
    
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.configure(text="▶️ Play")
            self.stop_timer()
        else:
            self.pause_button.configure(text="⏸️ Pause")
            # Resume slideshow
            # Still show the current image for the required interval
            self.current_index = (self.current_index - 1) % len(self.image_paths)
            self.show_next_image()
    
    def show_next_image(self):
        # Go to next image and schedule next update if not paused
        next_index = (self.current_index + 1) % len(self.image_paths)
        
        # If next image is not in cache, load it synchronously
        if next_index not in self.image_cache:
            image = self.load_image_sync(next_index)
            if image is None:
                # Skip to next if loading failed
                self.current_index = next_index
                self.timer_id = self.root.after(100, self.show_next_image)
                return
        
        self.current_index = next_index
        self.show_current_image()
        
        # Schedule next update only if not paused
        if not self.is_paused:
            self.timer_id = self.root.after(self.interval, self.show_next_image)
            
        # Preload next image in background
        self.preload_next_image()
    
    def show_settings(self):
        # Create settings dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry(f"{CONFIG_DLG_WIDTH}x{CONFIG_DLG_HEIGHT}")
        dialog.configure(bg='gray')
        dialog.attributes('-topmost', True)
        
        # Center the dialog on screen
        dialog.geometry("+%d+%d" % (
            self.root.winfo_screenwidth()/2 - CONFIG_DLG_WIDTH/2,
            self.root.winfo_screenheight()/2 - CONFIG_DLG_HEIGHT/2))
        
        # Create and pack widgets
        frame = tk.Frame(dialog, bg='gray', padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Interval label and spinbox
        label = tk.Label(frame, text="Interval (seconds):", 
                        bg='gray', fg='black',
                        font=('Arial', 14, 'bold'))
        label.pack(pady=(0, 10))
        
        spinbox = tk.Spinbox(frame, from_=1, to=60, 
                            width=10,
                            bg='white', fg='black',
                            insertbackground='black',
                            buttonbackground='lightgray',
                            font=('Arial', 14))
        spinbox.delete(0, tk.END)
        spinbox.insert(0, str(self.interval // 1000))
        spinbox.pack(pady=(0, 30))
        
        # Button frame
        btn_frame = tk.Frame(frame, bg='gray')
        btn_frame.pack()
        
        # Apply button
        apply_btn = tk.Button(btn_frame, text="Apply",
                            command=lambda: self.apply_settings(int(spinbox.get()) * 1000, dialog),
                            bg='lightgray', fg='black',
                            activebackground='white',
                            activeforeground='black',
                            font=('Arial', 12, 'bold'),
                            width=8)
        apply_btn.pack(side=tk.LEFT, padx=10)
        
        # Cancel button
        cancel_btn = tk.Button(btn_frame, text="Cancel",
                             command=dialog.destroy,
                             bg='lightgray', fg='black',
                             activebackground='white',
                             activeforeground='black',
                             font=('Arial', 12, 'bold'),
                             width=8)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def load_settings(self):
        # Default settings
        self.interval = 3000  # default 3 seconds
        self.window_size = (1024, 768)  # default window size
        self.is_fullscreen = False  # default to windowed mode
        
        # Try to load from config file
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)
            if 'Settings' in self.config:
                self.interval = self.config.getint('Settings', 'interval', fallback=3000)
                width = self.config.getint('Settings', 'window_width', fallback=1024)
                height = self.config.getint('Settings', 'window_height', fallback=768)
                self.window_size = (width, height)
                self.is_fullscreen = self.config.getboolean('Settings', 'is_fullscreen', fallback=False)
        else:
            # Create default config
            self.config['Settings'] = {
                'interval': self.interval,
                'window_width': self.window_size[0],
                'window_height': self.window_size[1],
                'is_fullscreen': str(self.is_fullscreen).lower()
            }
            with open(CONFIG_FILE, 'w') as f:
                self.config.write(f)
    
    def save_settings(self):
        self.config['Settings'] = {
            'interval': str(self.interval),
            'window_width': str(self.window_size[0]),
            'window_height': str(self.window_size[1]),
            'is_fullscreen': str(self.is_fullscreen).lower()
        }
        with open(CONFIG_FILE, 'w') as f:
            self.config.write(f)
    
    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if not self.is_fullscreen:
            # Store current screen position for restoring window
            screen_x = self.root.winfo_x()
            screen_y = self.root.winfo_y()
            # Switch to windowed mode
            self.root.attributes('-fullscreen', False)
            if not hasattr(self, 'window_size'):
                self.window_size = (1024, 768)
            # Center the window on screen
            x = (self.root.winfo_screenwidth() - self.window_size[0]) // 2
            y = (self.root.winfo_screenheight() - self.window_size[1]) // 2
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{x}+{y}")
        else:
            # Store current window size before going fullscreen
            self.window_size = (self.root.winfo_width(), self.root.winfo_height())
            self.root.attributes('-fullscreen', True)
        
        # Save both window size and fullscreen state
        self.save_settings()
        
        self.fullscreen_button.configure(text="⬜" if self.is_fullscreen else "🔲")
        # Update toolbar position for new window state
        self.root.update_idletasks()  # Ensure window metrics are updated
        # Update parent directory position
        self.update_parent_dir_position()
        # Force image resize
        self.show_current_image()
    
    def apply_settings(self, new_interval, dialog):
        self.interval = new_interval
        self.save_settings()
        dialog.destroy()
    
    def get_image_year(self, image_path):
        try:
            # Try to get year from EXIF data
            with Image.open(image_path) as img:
                exif = img.getexif()
                if exif:
                    # List of EXIF tags that might contain date information
                    date_tags = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized', 'CreateDate']
                    
                    # First try standard EXIF tags
                    for tag_id in ExifTags.TAGS:
                        tag_name = ExifTags.TAGS[tag_id]
                        if tag_name in date_tags and tag_id in exif:
                            # EXIF DateTime format: "YYYY:MM:DD HH:MM:SS"
                            return exif[tag_id][:4]
                    
                    # Then try extended EXIF tags
                    try:
                        exif_ifd = exif.get_ifd(0x8769)  # ExifIFD
                        if exif_ifd:
                            for tag_id in exif_ifd:
                                if ExifTags.TAGS.get(tag_id) in date_tags:
                                    return exif_ifd[tag_id][:4]
                    except:
                        pass
            
            # If no EXIF data, try modification time first, then creation time
            try:
                mtime = os.path.getmtime(image_path)
                return str(datetime.fromtimestamp(mtime).year)
            except:
                ctime = os.path.getctime(image_path)
                return str(datetime.fromtimestamp(ctime).year)
        except:
            return ""  # Return empty string if all methods fail

    def on_window_configure(self, event):
        # Only save window size if we're in windowed mode and the window was actually resized
        if not self.is_fullscreen and event.widget == self.root:
            new_size = (event.width, event.height)
            if hasattr(self, 'window_size') and self.window_size != new_size:
                self.window_size = new_size
                self.save_settings()
        
        # Update parent directory position
        self.update_parent_dir_position()
    
    def update_parent_dir_position(self):
        # Get window dimensions
        window_width = self.root.winfo_width()
        
        # Update parent directory text
        current_path = self.image_paths[self.current_index]
        parent_dir = os.path.basename(os.path.dirname(current_path))
        year = self.current_year
        
        # Format text with year if available
        display_text = f"{parent_dir} ({year})" if year else parent_dir
        self.parent_dir_label.configure(text=display_text)
        
        # Calculate position
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        
        # Calculate width based on text
        self.parent_dir_window.update_idletasks()
        required_width = self.parent_dir_label.winfo_reqwidth() + DIRNAME_PANEL_PADDING * 2
        
        if self.is_fullscreen:
            x_pos = window_width - required_width - DIRNAME_PANEL_MARGIN
            y_pos = DIRNAME_PANEL_MARGIN
        else:
            x_pos = root_x + window_width - required_width - DIRNAME_PANEL_MARGIN
            y_pos = root_y + DIRNAME_PANEL_MARGIN
        
        self.parent_dir_window.geometry(f'{required_width}x{DIRNAME_PANEL_HEIGHT}+{x_pos}+{y_pos}')
    
    def apply_exif_orientation(self, image):
        try:
            # Get EXIF data
            exif = image.getexif()
            if exif is None:
                return image

            # Get orientation tag
            orientation = exif.get(0x0112)  # 0x0112 is the orientation tag ID
            if orientation is None:
                return image

            # Apply orientation
            if orientation == 2:
                return image.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                return image.transpose(Image.ROTATE_180)
            elif orientation == 4:
                return image.transpose(Image.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                return image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
            elif orientation == 6:
                return image.transpose(Image.ROTATE_270)
            elif orientation == 7:
                return image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
            elif orientation == 8:
                return image.transpose(Image.ROTATE_90)
            return image
        except Exception as e:
            print(f"Error applying EXIF orientation: {e}")
            return image
    
    def extract_year_from_exif(self, image):
        """Try to get year from EXIF data"""
        try:
            exif = image.getexif()
            if not exif:
                return None

            # List of EXIF tags that might contain date information
            date_tags = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized', 'CreateDate']
            
            # First try standard EXIF tags
            for tag_id in ExifTags.TAGS:
                tag_name = ExifTags.TAGS[tag_id]
                if tag_name in date_tags and tag_id in exif:
                    # EXIF DateTime format: "YYYY:MM:DD HH:MM:SS"
                    return exif[tag_id][:4]
            
            # Then try extended EXIF tags
            exif_ifd = exif.get_ifd(0x8769)  # ExifIFD
            if exif_ifd:
                for tag_id in exif_ifd:
                    if ExifTags.TAGS.get(tag_id) in date_tags:
                        return exif_ifd[tag_id][:4]
        except:
            print(f"Error getting year from EXIF: {e}")
            return None

    def preload_next_image(self):
        """Queue the next image for background loading"""
        next_index = (self.current_index + 1) % len(self.image_paths)
        if next_index not in self.image_cache:
            self.load_queue.put(next_index)

    def background_loader(self):
        """Background thread for loading images"""
        while True:
            index = self.load_queue.get()
            if index not in self.image_cache:
                try:
                    # Load and process image
                    image = self.load_image_sync(index)
                    if image:
                        # Store in cache
                        self.image_cache[index] = image
                        print(f"Preloaded {self.image_paths[index]}")

                    # Remove old entries if cache is too large
                    if len(self.image_cache) > self.cache_size:
                        oldest = min(k for k in self.image_cache.keys() if k != self.current_index)
                        del self.image_cache[oldest]
                except Exception as e:
                    print(f"Error preloading image {self.image_paths[index]}: {e}")
            self.load_queue.task_done()

    def show_current_image(self):
        try:
            # Get image from cache or load it
            if self.current_index in self.image_cache:
                image = self.image_cache[self.current_index]
            else:
                # Load and process image if not in cache
                image = self.load_image_sync(self.current_index)
                if image is None:
                    raise Exception("Failed to load image")
            print(f"Shown {self.image_paths[self.current_index]}")

            # Update parent directory position when showing new image
            self.update_parent_dir_position()

            # Queue next image for loading
            self.preload_next_image()
            
            # Get dimensions based on mode
            if self.is_fullscreen:
                display_width = self.root.winfo_screenwidth()
                display_height = self.root.winfo_screenheight()
            else:
                # Use a default window size when switching to windowed mode
                if not hasattr(self, 'window_size'):
                    self.window_size = (1024, 768)
                    self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}")
                display_width = self.root.winfo_width()
                display_height = self.root.winfo_height()
            
            # Calculate aspect ratios
            image_ratio = image.width / image.height
            display_ratio = display_width / display_height
            
            if display_ratio > image_ratio:
                # Display is wider than image
                height = display_height
                width = int(height * image_ratio)
            else:
                # Display is taller than image
                width = display_width
                height = int(width / image_ratio)
            
            # Resize image
            image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Update label
            self.label.configure(image=photo)
            self.label.image = photo  # Keep a reference
            
        except Exception as e:
            error_msg = f"Error displaying image {self.image_paths[self.current_index]}: {e}"
            print(error_msg)
            
            # Create bad images file on first error if it doesn't exist
            if not self.bad_images_file:
                timestamp = self.start_timestamp.strftime("%Y%m%d_%H%M%S")
                self.bad_images_file = f"bad_images_{timestamp}.{DEF_EXT}"
                with open(self.bad_images_file, 'w') as f:
                    f.write("# Corrupted images log\n")
                    f.write(f"# Created: {self.start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Log error to bad images file
            with open(self.bad_images_file, 'a') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")
            
            # Skip to next image
            self.current_index = (self.current_index + 1) % len(self.image_paths)
            self.timer_id = self.root.after(100, self.show_next_image)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Photo slideshow application')
    parser.add_argument('photos_file', nargs='?', default=f'photos.{DEF_EXT}',
                      help=f'Path to the file containing photo paths (default: photos.{DEF_EXT})')
    parser.add_argument('--server', help='Server URL for remote slideshow mode')
    args = parser.parse_args()

    root = tk.Tk()
    photos_file = ensure_ext(args.photos_file)
    app = Slideshow(root, photos_file=photos_file, server_url=args.server)
    root.mainloop()

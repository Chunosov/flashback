import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from skimage import exposure
import os

def enhance_with_opencv(image_path, output_path):
    """
    Enhance image using OpenCV with automatic color correction and contrast enhancement
    """
    # Read image
    img = cv2.imread(image_path)
    
    # Convert to LAB color space
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    
    # Split channels
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    
    # Merge channels
    merged = cv2.merge((cl,a,b))
    
    # Convert back to BGR
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    
    # Denoise
    enhanced = cv2.fastNlMeansDenoisingColored(enhanced)
    
    # Save result
    cv2.imwrite(output_path, enhanced)

def enhance_with_pillow(image_path, output_path):
    """
    Enhance image using Pillow with auto-contrast and color enhancement
    """
    # Open image
    img = Image.open(image_path)
    
    # Auto-contrast
    img = ImageOps.autocontrast(img, cutoff=2)
    
    # Enhance color
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.2)  # Increase color saturation by 20%
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)  # Increase contrast by 10%
    
    # Enhance brightness
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)  # Increase brightness by 10%
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.2)  # Increase sharpness by 20%
    
    # Save result
    img.save(output_path)

def enhance_with_skimage(image_path, output_path):
    """
    Enhance image using scikit-image with advanced histogram equalization
    """
    # Read image
    img = cv2.imread(image_path)
    
    # Convert to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Perform adaptive histogram equalization
    img_adapted = exposure.equalize_adapthist(img_rgb, clip_limit=0.03)
    
    # Adjust gamma
    img_gamma = exposure.adjust_gamma(img_adapted, 1.2)
    
    # Convert back to BGR and save
    img_final = cv2.cvtColor((img_gamma * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, img_final)

def enhance_photo(input_path, output_dir="enhanced"):
    """
    Apply all enhancement methods and save results
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get filename without extension
    filename = os.path.splitext(os.path.basename(input_path))[0]
    
    # Apply each enhancement method
    try:
        enhance_with_opencv(input_path, os.path.join(output_dir, f"{filename}_opencv.jpg"))
        print(f"OpenCV enhancement saved for {filename}")
    except Exception as e:
        print(f"OpenCV enhancement failed: {e}")
    
    try:
        enhance_with_pillow(input_path, os.path.join(output_dir, f"{filename}_pillow.jpg"))
        print(f"Pillow enhancement saved for {filename}")
    except Exception as e:
        print(f"Pillow enhancement failed: {e}")
    
    try:
        enhance_with_skimage(input_path, os.path.join(output_dir, f"{filename}_skimage.jpg"))
        print(f"Scikit-image enhancement saved for {filename}")
    except Exception as e:
        print(f"Scikit-image enhancement failed: {e}")

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        input_image = sys.argv[1]
        enhance_photo(input_image)
        print(f"\nEnhanced versions have been saved in the 'enhanced' directory")
    else:
        print("Please provide an image path as argument")
        print("Usage: python enhance_photos.py path/to/image.jpg")

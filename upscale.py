import os
from pathlib import Path
import cv2
import numpy as np
from realesrgan_ncnn_py import Realesrgan

def upscale_image(input_path, output_path=None, scale=4, model_name='realesrnet-x4plus', gpu_id=0):
    """
    Upscale an image using Real-ESRGAN.
    
    Args:
        input_path (str): Path to the input image
        output_path (str, optional): Path to save the output image. If None,
            will append '_upscaled' to the input filename
        scale (int, optional): Upscaling factor (2, 3, or 4). Default is 4
        model_name (str, optional): Model to use. Options:
            - 'realesrgan-x4plus' (default, good for general images)
            - 'realesrnet-x4plus' (sharper but may have more artifacts)
            - 'realesrgan-x4plus-anime' (optimized for anime/art)
    
    Returns:
        str: Path to the upscaled image
    """
    # Validate input path
    if not os.path.exists(input_path):
        raise ValueError(f"Input file not found: {input_path}")
    
    # Generate output path if not provided
    if output_path is None:
        input_path = Path(input_path)
        output_path = input_path.parent / f"{input_path.stem}_upscaled{input_path.suffix}"
    
    # Create upscaler instance
    upscaler = Realesrgan(gpuid=gpu_id)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    try:
        # Read image
        img = cv2.imread(str(input_path))
        if img is None:
            raise ValueError(f"Could not read image: {input_path}")
        
        # Process image using cv2 method
        result_img = upscaler.process_cv2(img)
        
        # Save result
        cv2.imwrite(str(output_path), result_img)
        print(f"Successfully upscaled image: {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"Error upscaling image {input_path}: {e}")
        raise

def batch_upscale(input_dir, output_dir=None, scale=4, model_name='realesrgan-x4plus'):
    """
    Upscale all images in a directory.
    
    Args:
        input_dir (str): Directory containing input images
        output_dir (str, optional): Directory to save upscaled images
        scale (int, optional): Upscaling factor (2, 3, or 4). Default is 4
        model_name (str, optional): Model to use (see upscale_image for options)
    
    Returns:
        list: Paths to all upscaled images
    """
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise ValueError(f"Input directory not found: {input_dir}")
    
    # Set output directory
    if output_dir is None:
        output_dir = input_dir / 'upscaled'
    output_dir = Path(output_dir)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all images
    upscaled_images = []
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    for file in input_dir.rglob('*'):
        if file.suffix.lower() in image_extensions:
            try:
                output_path = output_dir / file.relative_to(input_dir)
                upscaled_path = upscale_image(
                    str(file),
                    str(output_path),
                    scale=scale,
                    model_name=model_name
                )
                upscaled_images.append(upscaled_path)
            except Exception as e:
                print(f"Error processing {file}: {e}")
    
    return upscaled_images

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Upscale images using Real-ESRGAN')
    parser.add_argument('input', help='Input image or directory')
    parser.add_argument('-o', '--output', help='Output path (optional)')
    parser.add_argument('-s', '--scale', type=int, choices=[2, 3, 4], default=4,
                       help='Upscaling factor (default: 4)')
    parser.add_argument('-m', '--model', default='realesrgan-x4plus',
                       choices=['realesrgan-x4plus', 'realesrnet-x4plus', 'realesrgan-x4plus-anime'],
                       help='Model to use (default: realesrgan-x4plus)')
    
    args = parser.parse_args()
    
    try:
        input_path = Path(args.input)
        if input_path.is_file():
            upscale_image(args.input, args.output, args.scale, args.model)
        else:
            batch_upscale(args.input, args.output, args.scale, args.model)
    except Exception as e:
        print(f"Error: {e}")

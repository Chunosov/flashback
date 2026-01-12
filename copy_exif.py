#!/usr/bin/env python3
"""
Script to copy EXIF data from RAW image files to processed JPG files.

Usage:
    python copy_exif.py <raw_directory> <jpg_directory>

For each raw file in the raw directory, the script finds the corresponding JPG file
in the jpg directory and copies EXIF data from the raw to the JPG without recompressing
the image.
"""

import argparse
import os
import sys
from pathlib import Path
import piexif

# Raw file extension (case-insensitive pattern to avoid duplicates on Windows)
RAW_EXT = "*.[Nn][Ee][Ff]"

# Whitelisted EXIF tags for 0th IFD (Image metadata)
# Note: Orientation is excluded because JPG files are typically already rotated during processing,
# while raw files store sensor data with orientation flag. Copying orientation would apply rotation twice.
EXIF_0TH_WHITELIST = [
    piexif.ImageIFD.Make,
    piexif.ImageIFD.Model,
    piexif.ImageIFD.Software,
    piexif.ImageIFD.DateTime,
    piexif.ImageIFD.XResolution,
    piexif.ImageIFD.YResolution,
    piexif.ImageIFD.ResolutionUnit,
    piexif.ImageIFD.Copyright,
    piexif.ImageIFD.Artist,
]

# Whitelisted EXIF tags for Exif IFD (Photo shooting parameters)
EXIF_WHITELIST = [
    piexif.ExifIFD.DateTimeOriginal,
    piexif.ExifIFD.DateTimeDigitized,
    piexif.ExifIFD.ExposureTime,
    piexif.ExifIFD.FNumber,
    piexif.ExifIFD.ISOSpeedRatings,
    piexif.ExifIFD.ExposureProgram,
    piexif.ExifIFD.MeteringMode,
    piexif.ExifIFD.Flash,
    piexif.ExifIFD.FocalLength,
    piexif.ExifIFD.FocalLengthIn35mmFilm,
    piexif.ExifIFD.ExposureBiasValue,
    piexif.ExifIFD.LensModel,
    piexif.ExifIFD.LensMake,
    piexif.ExifIFD.WhiteBalance,
    piexif.ExifIFD.ColorSpace,
    piexif.ExifIFD.LightSource,
    piexif.ExifIFD.ExifVersion,
    piexif.ExifIFD.FlashpixVersion,
    piexif.ExifIFD.ComponentsConfiguration,
    piexif.ExifIFD.CompressedBitsPerPixel,
    piexif.ExifIFD.ShutterSpeedValue,
    piexif.ExifIFD.ApertureValue,
    piexif.ExifIFD.BrightnessValue,
    piexif.ExifIFD.MaxApertureValue,
    piexif.ExifIFD.SubjectDistance,
    piexif.ExifIFD.SubjectDistanceRange,
    piexif.ExifIFD.SceneCaptureType,
    piexif.ExifIFD.GainControl,
    piexif.ExifIFD.Contrast,
    piexif.ExifIFD.Saturation,
    piexif.ExifIFD.Sharpness,
    piexif.ExifIFD.SubjectArea,
    piexif.ExifIFD.SensingMethod,
    piexif.ExifIFD.FileSource,
    piexif.ExifIFD.SceneType,
    piexif.ExifIFD.CustomRendered,
    piexif.ExifIFD.ExposureMode,
    piexif.ExifIFD.DigitalZoomRatio,
]


def find_matching_jpg(raw_path, jpg_dir):
    """
    Find a JPG file that matches the given raw file.
    
    JPG files may have the same base name or include suffixes like:
    - DSC_0707.NEF -> DSC_0707.jpg
    - DSC_0707.NEF -> DSC_0707_1.jpg
    - DSC_0707.NEF -> DSC_0707_enhanced.jpg
    
    Args:
        raw_path: Path to the raw file
        jpg_dir: Directory containing JPG files
        
    Returns:
        Path to matching JPG file or None if not found
    """
    raw_name = Path(raw_path).stem  # e.g., "DSC_0707"
    jpg_directory = Path(jpg_dir)
    
    # Look for exact match first
    exact_match = jpg_directory / f"{raw_name}.jpg"
    if exact_match.exists():
        return exact_match
    
    # Case-insensitive exact match
    exact_match_upper = jpg_directory / f"{raw_name}.JPG"
    if exact_match_upper.exists():
        return exact_match_upper
    
    # Look for files with suffixes (e.g., DSC_0707_1.jpg, DSC_0707-enhanced.jpg)
    for jpg_file in jpg_directory.glob(f"{raw_name}[_-]*.[Jj][Pp][Gg]"):
        return jpg_file
    
    return None


def jpg_has_exif(jpg_path):
    """
    Check if a JPG file already has EXIF data.
    
    Args:
        jpg_path: Path to the JPG file
        
    Returns:
        True if JPG has EXIF data, False otherwise
    """
    try:
        exif_dict = piexif.load(str(jpg_path))
        # Check if any EXIF IFD has data (excluding thumbnail)
        has_data = (
            len(exif_dict.get("0th", {})) > 0 or
            len(exif_dict.get("Exif", {})) > 0 or
            len(exif_dict.get("GPS", {})) > 0 or
            len(exif_dict.get("1st", {})) > 0
        )
        return has_data
    except Exception:
        return False


def copy_exif(raw_path, jpg_path):
    """
    Copy EXIF data from raw image to JPG file without recompressing the image.
    Uses a whitelist approach to only copy photography-relevant tags.
    
    Args:
        raw_path: Path to the source raw image
        jpg_path: Path to the destination JPG file
        
    Returns:
        None if successful, error message string otherwise
    """
    try:
        # Read EXIF data from raw file
        raw_exif = piexif.load(str(raw_path))
        
        # Create a new EXIF dictionary with only safe, relevant tags
        new_exif = {"0th": {}, "Exif": {}, "GPS": {}}
        
        # Copy whitelisted tags from 0th IFD
        if "0th" in raw_exif:
            for tag in EXIF_0TH_WHITELIST:
                if tag in raw_exif["0th"]:
                    new_exif["0th"][tag] = raw_exif["0th"][tag]
        
        # Copy whitelisted tags from Exif IFD
        if "Exif" in raw_exif:
            for tag in EXIF_WHITELIST:
                if tag in raw_exif["Exif"]:
                    new_exif["Exif"][tag] = raw_exif["Exif"][tag]
        
        # Copy all GPS tags (they are generally safe)
        if "GPS" in raw_exif and len(raw_exif["GPS"]) > 0:
            new_exif["GPS"] = raw_exif["GPS"].copy()
        
        # Add comment about the source
        comment = f"Copied from {Path(raw_path).name}".encode('utf-8')
        new_exif["Exif"][piexif.ExifIFD.UserComment] = comment
        
        # Add ImageDescription with source file name
        new_exif["0th"][piexif.ImageIFD.ImageDescription] = f"Copied from {Path(raw_path).name}".encode('ascii')
        
        # Convert EXIF dict to bytes
        exif_bytes = piexif.dump(new_exif)
        
        # Insert EXIF data into JPG without recompressing
        # This preserves the original JPG quality
        piexif.insert(exif_bytes, str(jpg_path))

        return None
        
    except Exception as e:
        return f"  ERROR: Failed to copy EXIF data: {e}"

stats = {
    'processed': 0,
    'skipped_has_exif': 0,
    'skipped_no_match': 0,
    'failed': 0
}

def process_raw_file(raw_file: Path, jpg_path: Path, force_overwrite: bool, copy_datetime: bool):
    """
    Process raw image and copy EXIF to matching JPG file.
    
    Args:
        raw_file: Path to raw image
        jpg_path: Path containing processed JPG files
        force_overwrite: If True, overwrite EXIF even if JPG already has EXIF data
        copy_datetime: If True, copy file creation and modification timestamps
    """
    raw_name = raw_file.name
    msgs = [f"Processing: {raw_name}"]
    #print(f"Processing: {raw_name}")

    # Find matching JPG file
    jpg_file = find_matching_jpg(raw_file, jpg_path)
    
    if jpg_file is None:
        #print(f"  SKIPPED: No matching JPG file found")
        stats['skipped_no_match'] += 1
        return []
    
    msgs.append(f"  Found JPG: {jpg_file.name}")
    
    # Check if JPG already has EXIF data (unless force_overwrite is enabled)
    if not force_overwrite and jpg_has_exif(jpg_file):
        msgs.append(f"  SKIPPED: JPG already contains EXIF data")
        stats['skipped_has_exif'] += 1
        return msgs
    
    # Copy EXIF data
    res = copy_exif(raw_file, jpg_file)
    if res is None:
        msgs.append(f"  SUCCESS: EXIF data copied to {jpg_file.name}")
        stats['processed'] += 1
        
        # Copy file timestamps if requested
        if copy_datetime:
            try:
                raw_stat = raw_file.stat()
                # Set access time and modification time
                os.utime(str(jpg_file), (raw_stat.st_atime, raw_stat.st_mtime))
                msgs.append(f"  SUCCESS: File timestamps copied")
            except Exception as e:
                msgs.append(f"  WARNING: Failed to copy timestamps: {e}")
    else:
        msgs.append(res)
        stats['failed'] += 1

    return msgs


def process_directories(raw_dir, jpg_dir, force_overwrite, copy_datetime):
    """
    Process all files in the raw directory and copy EXIF to matching JPG files.
    
    Args:
        raw_dir: Directory containing RAW image files
        jpg_dir: Directory containing processed JPG files
        force_overwrite: If True, overwrite EXIF even if JPG already has EXIF data
        copy_datetime: If True, copy file creation and modification timestamps
    """
    raw_path = Path(raw_dir)
    jpg_path = Path(jpg_dir)
    
    # Validate directories
    if not raw_path.exists():
        print(f"ERROR: Raw directory does not exist: {raw_dir}")
        sys.exit(1)
    
    if not jpg_path.exists():
        print(f"ERROR: JPG directory does not exist: {jpg_dir}")
        sys.exit(1)
    
    # Find all raw images
    raw_files = list(raw_path.glob(RAW_EXT))
    
    if not raw_files:
        print(f"No raw files found in {raw_dir}")
        return
    
    print(f"Found {len(raw_files)} raw files in {raw_dir}")
    print(f"Processing...\n")
    
    for raw_file in sorted(raw_files):
        msgs = process_raw_file(raw_file, jpg_path, force_overwrite, copy_datetime)
        for m in msgs:
            print(m)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  Total raw files: {len(raw_files)}")
    print(f"  Successfully processed: {stats['processed']}")
    print(f"  Skipped (already has EXIF): {stats['skipped_has_exif']}")
    print(f"  Skipped (no matching JPG): {stats['skipped_no_match']}")
    print(f"  Failed: {stats['failed']}")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Copy EXIF data from RAW image files to processed JPG files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python copy_exif.py ./raw_photos ./processed_photos
  python copy_exif.py "C:/Photos/RAW" "C:/Photos/Processed"
  python copy_exif.py ./raw_photos ./processed_photos --force
  python copy_exif.py ./raw_photos ./processed_photos --datetime
  python copy_exif.py ./raw_photos ./processed_photos --force --datetime
        """
    )
    
    parser.add_argument(
        'raw_dir',
        help='Directory containing source RAW image files'
    )
    
    parser.add_argument(
        'jpg_dir',
        help='Directory containing processed JPG files'
    )
    
    parser.add_argument(
        '--force',
        '-f',
        action='store_true',
        help='Force overwrite EXIF data even if JPG already contains EXIF'
    )
    
    parser.add_argument(
        '--datetime',
        '-d',
        action='store_true',
        help='Copy file creation and modification timestamps from raw to JPG'
    )
    
    args = parser.parse_args()
    
    process_directories(args.raw_dir, args.jpg_dir, args.force, args.datetime)


if __name__ == "__main__":
    main()

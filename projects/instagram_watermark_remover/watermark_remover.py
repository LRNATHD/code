"""Watermark detection and removal using OpenCV inpainting (and optionally IOPaint/Lama model)."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import tempfile
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2

from config import (
    USE_GPU,
    WATERMARK_POSITION,
    WATERMARK_REGIONS,
    PROCESSED_DIR,
    TEMP_DIR,
    MAX_IMAGE_SIZE,
)


class WatermarkRemover:
    """Handles watermark detection and removal using OpenCV inpainting (and optionally IOPaint)."""
    
    def __init__(self):
        self.device = "cuda" if USE_GPU else "cpu"
        self._check_iopaint_installed()
    
    def _check_iopaint_installed(self):
        """Check if IOPaint is installed (optional, for better quality)."""
        try:
            import iopaint
            self.iopaint_available = True
            print("IOPaint available - will use LaMa model for high quality inpainting.")
        except ImportError:
            self.iopaint_available = False
            print("IOPaint not installed - using OpenCV inpainting (still works well for watermarks).")
    
    def detect_watermark_region(
        self,
        image_path: Path,
        position: str = "auto"
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect the region containing the Instagram watermark.
        
        Returns: Tuple of (x1, y1, x2, y2) or None if not found.
        """
        img = Image.open(image_path)
        width, height = img.size
        
        if position == "auto":
            # Try to detect watermark in common positions
            # Instagram watermarks are usually in bottom corners
            positions_to_check = ["bottom_right", "bottom_left", "top_right", "top_left"]
            
            for pos in positions_to_check:
                region = self._get_region_coords(width, height, pos)
                if self._check_for_watermark(img, region):
                    return region
            
            # Default to bottom right if no detection
            return self._get_region_coords(width, height, "bottom_right")
        else:
            return self._get_region_coords(width, height, position)
    
    def _get_region_coords(
        self,
        width: int,
        height: int,
        position: str
    ) -> Tuple[int, int, int, int]:
        """Get pixel coordinates for a watermark region."""
        if position not in WATERMARK_REGIONS:
            position = "bottom_right"
        
        region = WATERMARK_REGIONS[position]
        
        x1 = int(width * region["x_start"])
        y1 = int(height * region["y_start"])
        x2 = int(width * region["x_end"])
        y2 = int(height * region["y_end"])
        
        return (x1, y1, x2, y2)
    
    def _check_for_watermark(
        self,
        img: Image.Image,
        region: Tuple[int, int, int, int]
    ) -> bool:
        """
        Check if a region likely contains a watermark.
        Uses simple heuristics based on text-like patterns.
        """
        x1, y1, x2, y2 = region
        roi = img.crop((x1, y1, x2, y2))
        
        # Convert to grayscale numpy array
        roi_gray = np.array(roi.convert("L"))
        
        # Look for high contrast areas (text tends to have sharp edges)
        # Using edge detection
        edges = cv2.Canny(roi_gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Watermarks typically have moderate edge density (text)
        return edge_density > 0.02 and edge_density < 0.3
    
    def create_mask(
        self,
        image_path: Path,
        region: Tuple[int, int, int, int],
        padding: int = 10
    ) -> Path:
        """
        Create a mask image for the watermark region.
        White pixels indicate areas to inpaint.
        """
        img = Image.open(image_path)
        width, height = img.size
        
        # Create black mask (0 = keep, 255 = inpaint)
        mask = Image.new("L", (width, height), 0)
        
        x1, y1, x2, y2 = region
        
        # Add padding
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)
        
        # Draw white rectangle for watermark area
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        draw.rectangle([x1, y1, x2, y2], fill=255)
        
        # Save mask
        mask_path = TEMP_DIR / f"{image_path.stem}_mask.png"
        mask.save(mask_path)
        
        return mask_path
    
    def create_custom_mask(
        self,
        image_path: Path,
        mask_regions: List[Tuple[int, int, int, int]]
    ) -> Path:
        """Create a mask with multiple regions."""
        img = Image.open(image_path)
        width, height = img.size
        
        mask = Image.new("L", (width, height), 0)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        
        for region in mask_regions:
            x1, y1, x2, y2 = region
            draw.rectangle([x1, y1, x2, y2], fill=255)
        
        mask_path = TEMP_DIR / f"{image_path.stem}_custom_mask.png"
        mask.save(mask_path)
        
        return mask_path
    
    def remove_watermark(
        self,
        image_path: Path,
        mask_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
        position: str = "auto"
    ) -> Optional[Path]:
        """
        Remove watermark from an image.
        
        Uses IOPaint/LaMa if available, otherwise falls back to OpenCV inpainting.
        
        Args:
            image_path: Path to the input image
            mask_path: Path to mask image (optional, will be generated if not provided)
            output_path: Path for output image (optional)
            position: Watermark position hint
            
        Returns:
            Path to the processed image or None if failed
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            print(f"Image not found: {image_path}")
            return None
        
        # Generate mask if not provided
        if mask_path is None:
            region = self.detect_watermark_region(image_path, position)
            if region is None:
                print("Could not detect watermark region")
                return None
            mask_path = self.create_mask(image_path, region)
        
        # Set output path
        if output_path is None:
            output_path = PROCESSED_DIR / f"{image_path.stem}_cleaned{image_path.suffix}"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        generated_mask = TEMP_DIR in mask_path.parents or mask_path.parent == TEMP_DIR
        
        try:
            # Try IOPaint first if available (better quality)
            if self.iopaint_available:
                result = self._run_iopaint(image_path, mask_path, output_path)
                if result:
                    if generated_mask:
                        mask_path.unlink(missing_ok=True)
                    return result
            
            # Fallback to OpenCV inpainting (always works)
            print("Using OpenCV inpainting...")
            result = self._opencv_inpaint(image_path, mask_path, output_path)
            
            if generated_mask:
                mask_path.unlink(missing_ok=True)
            
            return result
            
        except Exception as e:
            print(f"Error removing watermark: {e}")
            if generated_mask:
                mask_path.unlink(missing_ok=True)
            return None
    
    def _run_iopaint(
        self,
        image_path: Path,
        mask_path: Path,
        output_path: Path
    ) -> Optional[Path]:
        """Run IOPaint to process the image."""
        # Create temp directory for IOPaint processing
        temp_output_dir = TEMP_DIR / "iopaint_output"
        temp_output_dir.mkdir(exist_ok=True)
        
        # Copy image and mask to temp locations with matching names
        temp_image = TEMP_DIR / "input.png"
        temp_mask = TEMP_DIR / "input_mask.png"
        
        # Convert and save as PNG for consistency
        Image.open(image_path).save(temp_image)
        Image.open(mask_path).save(temp_mask)
        
        try:
            # Run IOPaint CLI
            cmd = [
                sys.executable, "-m", "iopaint", "run",
                "--model", "lama",
                "--device", self.device,
                "--image", str(temp_image),
                "--mask", str(temp_mask),
                "--output", str(temp_output_dir)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                # Try alternative approach using Python API
                return self._run_iopaint_api(temp_image, temp_mask, output_path)
            
            # Find output file
            output_files = list(temp_output_dir.glob("*"))
            if output_files:
                shutil.copy(output_files[0], output_path)
                return output_path
            
        except subprocess.TimeoutExpired:
            print("IOPaint processing timed out")
        except Exception as e:
            print(f"CLI failed, trying API: {e}")
            return self._run_iopaint_api(temp_image, temp_mask, output_path)
        finally:
            # Cleanup temp files
            temp_image.unlink(missing_ok=True)
            temp_mask.unlink(missing_ok=True)
            shutil.rmtree(temp_output_dir, ignore_errors=True)
        
        return None
    
    def _run_iopaint_api(
        self,
        image_path: Path,
        mask_path: Path,
        output_path: Path
    ) -> Optional[Path]:
        """Run IOPaint using Python API directly."""
        try:
            from iopaint import Inpainter
            from iopaint.model_manager import ModelManager
            
            # Load the LaMa model
            model = ModelManager.get_model("lama", self.device)
            inpainter = Inpainter(model)
            
            # Load image and mask
            image = np.array(Image.open(image_path).convert("RGB"))
            mask = np.array(Image.open(mask_path).convert("L"))
            
            # Run inpainting
            result = inpainter.inpaint(image, mask)
            
            # Save result
            Image.fromarray(result).save(output_path)
            
            return output_path
        except Exception as e:
            print(f"IOPaint API failed: {e}")
            # Fallback to simple inpainting with OpenCV
            return self._opencv_inpaint(image_path, mask_path, output_path)
    
    def _opencv_inpaint(
        self,
        image_path: Path,
        mask_path: Path,
        output_path: Path
    ) -> Optional[Path]:
        """Fallback inpainting using OpenCV's Telea method."""
        try:
            image = cv2.imread(str(image_path))
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            
            # Use Telea inpainting (good for small regions)
            result = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            
            cv2.imwrite(str(output_path), result)
            return output_path
        except Exception as e:
            print(f"OpenCV inpainting failed: {e}")
            return None
    
    def batch_process(
        self,
        image_paths: List[Path],
        position: str = "auto",
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Process multiple images.
        
        Args:
            image_paths: List of image paths to process
            position: Watermark position hint
            callback: Optional callback function(current, total, status)
            
        Returns:
            Dictionary with processing results
        """
        results = {
            "total": len(image_paths),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "processed_files": [],
            "failed_files": [],
        }
        
        for i, image_path in enumerate(image_paths):
            if callback:
                callback(i + 1, len(image_paths), f"Processing {image_path.name}")
            
            try:
                output_path = self.remove_watermark(image_path, position=position)
                
                if output_path and output_path.exists():
                    results["success"] += 1
                    results["processed_files"].append({
                        "input": str(image_path),
                        "output": str(output_path)
                    })
                else:
                    results["failed"] += 1
                    results["failed_files"].append(str(image_path))
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                results["failed"] += 1
                results["failed_files"].append(str(image_path))
        
        return results


# Global remover instance
watermark_remover = WatermarkRemover()

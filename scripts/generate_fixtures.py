#!/usr/bin/env python3
"""
SatQuery AI — Synthetic Test Fixtures Generator
Generates small synthetic test files for testing Phase 1 geospatial ingestion:
- geotiff_valid.tif (GeoTIFF with CRS EPSG:4326, affine geotransform, 4 bands uint16)
- tiff_no_crs.tif (Standard TIFF, 3 bands uint8, no geospatial tags)
- sample.png (Standard RGB PNG)
- sample.jpg (Standard RGB JPEG)
- corrupted.tif (Invalid/corrupted header)
- invalid.txt (Unsupported extension)
"""

import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"

def generate_fixtures():
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating synthetic test fixtures in: {FIXTURES_DIR}")

    # 1. GeoTIFF valid (with CRS and Affine Transform)
    geotiff_path = FIXTURES_DIR / "geotiff_valid.tif"
    try:
        import rasterio
        from rasterio.transform import from_origin

        width, height = 128, 128
        transform = from_origin(77.5946, 12.9716, 0.0001, 0.0001)  # Bengaluru coords
        # 4 bands: B, G, R, NIR (Sentinel-like 16-bit simulated values)
        data = np.zeros((4, height, width), dtype=np.uint16)
        for b in range(4):
            x = np.linspace(1000, 5000, width)
            y = np.linspace(1000, 5000, height)
            xx, yy = np.meshgrid(x, y)
            data[b] = ((xx + yy) * (b + 1) / 4).astype(np.uint16)

        with rasterio.open(
            geotiff_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=4,
            dtype='uint16',
            crs='EPSG:4326',
            transform=transform,
            nodata=0
        ) as dst:
            dst.write(data)
        print(f" [OK] Created valid GeoTIFF: {geotiff_path.name}")
    except ImportError:
        # Fallback using PIL if rasterio is not installed on host
        img_array = (np.random.rand(100, 100, 3) * 255).astype(np.uint8)
        img = Image.fromarray(img_array)
        img.save(geotiff_path, format="TIFF")
        print(f" [!] Rasterio not present on host; created fallback TIFF: {geotiff_path.name}")

    # 2. Standard TIFF without CRS
    tiff_no_crs_path = FIXTURES_DIR / "tiff_no_crs.tif"
    arr = (np.random.rand(128, 128, 3) * 255).astype(np.uint8)
    img_no_crs = Image.fromarray(arr)
    img_no_crs.save(tiff_no_crs_path, format="TIFF")
    print(f" [OK] Created non-georeferenced TIFF: {tiff_no_crs_path.name}")

    # 3. Sample PNG
    png_path = FIXTURES_DIR / "sample.png"
    arr_png = (np.random.rand(96, 96, 3) * 255).astype(np.uint8)
    img_png = Image.fromarray(arr_png)
    img_png.save(png_path, format="PNG")
    print(f" [OK] Created sample PNG: {png_path.name}")

    # 4. Sample JPEG
    jpg_path = FIXTURES_DIR / "sample.jpg"
    arr_jpg = (np.random.rand(96, 96, 3) * 255).astype(np.uint8)
    img_jpg = Image.fromarray(arr_jpg)
    img_jpg.save(jpg_path, format="JPEG", quality=90)
    print(f" [OK] Created sample JPEG: {jpg_path.name}")

    # 5. Corrupted TIFF
    corrupt_path = FIXTURES_DIR / "corrupted.tif"
    with open(corrupt_path, "wb") as f:
        # Broken TIFF header (starts with II* but truncated/scrambled)
        f.write(b"II*\x00\xff\xfe\x00\x00\x12\x34garbagecorruptdatarasterfailure")
    print(f" [OK] Created corrupted fixture: {corrupt_path.name}")

    # 6. Invalid file extension
    txt_path = FIXTURES_DIR / "invalid.txt"
    with open(txt_path, "w") as f:
        f.write("This is a plain text file that should be rejected by SatQuery AI.")
    print(f" [OK] Created invalid extension fixture: {txt_path.name}")

    print("All fixtures generated successfully.")

if __name__ == "__main__":
    generate_fixtures()

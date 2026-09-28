# SatQuery AI — Geospatial & Raster Processing Engine

**Project:** SatQuery AI  
**Subsystem:** Geospatial Processing Engine (`backend/app/geospatial/`)  
**Core Dependencies:** `rasterio>=1.3.9`, `gdal-bin`, `libgdal-dev`, `pyproj>=3.6.1`, `numpy>=1.26.0`, `Pillow>=10.2.0`  

---

## 1. Principles of Satellite Geospatial Processing

Standard computer vision frameworks treat images as simple 8-bit RGB pixel grids $[0, 255]^{H \times W \times 3}$. Satellite remote sensing requires a fundamentally different approach:
1. **Never Assume EPSG:4326:** Satellite rasters are commonly projected in Universal Transverse Mercator (UTM) zones (e.g. `EPSG:32643`), Lambert Conformal Conic, or polar stereographic projections to preserve metric distances and surface areas.
2. **Preserve Affine Geotransforms:** Converting pixel offsets $(x, y)$ to real-world coordinates $(X, Y)$ requires the 6-parameter affine transformation matrix:
   $$\begin{pmatrix} X \\ Y \end{pmatrix} = \begin{pmatrix} c & a \\ f & e \end{pmatrix} \begin{pmatrix} x \\ y \end{pmatrix} + \begin{pmatrix} c \\ f \end{pmatrix}$$
3. **High-Dynamic-Range Radiometry:** Satellite sensors capture 12-bit to 16-bit surface reflectance (values from 0 to 65,535). Naive conversion to 8-bit uint8 clips critical ground features into black or white saturation.
4. **NoData Masking:** Edge swaths, orbital fringes, and missing scan lines use explicit NoData values (e.g., `0`, `-9999`, `nan`) that must be excluded from calculations.

---

## 2. Core Modules in `backend/app/geospatial/`

| Module | Core Class / Functions | Responsibilities |
| :--- | :--- | :--- |
| `reader.py` | `SafeRasterReader` | Memory-safe raster reading, GDAL overview detection, windowed reads for large files, decompression bomb safeguards. |
| `metadata.py` | `MetadataExtractor` | Extracts band count, data type, dimensions, CRS, EPSG code, affine transform, spatial resolution, and bounding coordinates. |
| `normalization.py` | `RadiometricNormalizer` | Dynamic percentile-based radiometric contrast stretching (2%–98%), multi-band RGB compositing. |
| `preview.py` | `PreviewGenerator` | Generates high-fidelity, downsampled RGB PNG previews (capped at 2048px) for low-latency web browser viewing. |
| `validator.py` | `GeospatialValidator` | Magic byte header sniffing, dimension bounds checking, format validation, and security sanitization. |

---

## 3. Metadata Extraction Pipeline (`metadata.py`)

When an uploaded file is ingested, `MetadataExtractor.extract(dataset)` extracts complete technical specifications:

```json
{
  "format": "GeoTIFF",
  "size_bytes": 14285714,
  "raster": {
    "width": 2048,
    "height": 2048,
    "bands": 4,
    "dtype": "uint16",
    "nodata": 0.0
  },
  "geospatial": {
    "is_geospatial": true,
    "crs": "EPSG:32643",
    "epsg": 32643,
    "proj4": "+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs",
    "transform": [10.0, 0.0, 72.100, 0.0, -10.0, 21.200],
    "resolution": {
      "x": 10.0,
      "y": 10.0,
      "unit": "metre"
    },
    "bounds": {
      "left": 72.100,
      "bottom": 21.100,
      "right": 72.200,
      "top": 21.200
    }
  }
}
```

---

## 4. Radiometric Normalization (`normalization.py`)

To prepare multi-spectral 16-bit satellite rasters for AI model backbones (which expect normalized $[0, 1]$ or $[0, 255]$ floats) and web browsers:

```python
def normalize_band_percentile(band: np.ndarray, lower_pct: float = 2.0, upper_pct: float = 98.0) -> np.ndarray:
    valid_mask = ~np.isnan(band)
    if band.dtype == np.uint16:
        valid_mask &= (band > 0)
    
    if not np.any(valid_mask):
        return np.zeros_like(band, dtype=np.uint8)

    p_low = np.percentile(band[valid_mask], lower_pct)
    p_high = np.percentile(band[valid_mask], upper_pct)

    if p_high <= p_low:
        p_high = p_low + 1.0

    clipped = np.clip(band, p_low, p_high)
    normalized = ((clipped - p_low) / (p_high - p_low) * 255.0).astype(np.uint8)
    return normalized
```

---

## 5. Coordinate Systems & Transformations

SatQuery AI manages three distinct coordinate frames:

```mermaid
flowchart LR
    NORM["Normalized Relative Coordinates<br/>[ymin, xmin, ymax, xmax] in [0, 1]"] <-->|Image Dimensions (W, H)| PIX["Pixel Coordinates<br/>(x, y) in integer pixels"]
    PIX <-->|Affine Geotransform Matrix| NATIVE["Native CRS Coordinates<br/>(Easting, Northing) in EPSG:32643 (UTM)"]
    NATIVE <-->|PyProj Reprojection| WGS84["Geographic Coordinates<br/>(Longitude, Latitude) in EPSG:4326"]
```

### Coordinate Conversion Formulas:
1. **Normalized $[0, 1]$ to Pixel:**
   $$x = \text{xmin} \cdot W, \quad y = \text{ymin} \cdot H$$
2. **Pixel to Native CRS:**
   $$X_{\text{native}} = \text{transform}[2] + x \cdot \text{transform}[0] + y \cdot \text{transform}[1]$$
   $$Y_{\text{native}} = \text{transform}[5] + x \cdot \text{transform}[3] + y \cdot \text{transform}[4]$$
3. **Native CRS to Geographic WGS84 (`EPSG:4326`):**
   Computed dynamically via `pyproj.Transformer.from_crs(native_crs, "EPSG:4326", always_xy=True)`.

---

## 6. Spatial Alignment & Resampling in Temporal/Cross-Modal Pairs

When comparing two rasters ($T_1$ and $T_2$ or Optical and SAR):
1. **CRS Check:** If CRS differs, `TemporalAlignmentService` reprojects the secondary raster into the primary CRS.
2. **Resolution Matching:** Resamples pixel grids using bilinear interpolation for continuous reflectance data or nearest neighbor for discrete categorical masks.
3. **Bounds Intersection:** Computes the bounding box intersection $[\max(L_1, L_2), \max(B_1, B_2), \min(R_1, R_2), \min(T_1, T_2)]$. If the intersection area is less than 10%, raises `ALIGNMENT_FAILURE`.

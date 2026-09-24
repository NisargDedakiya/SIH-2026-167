"""
Remote-Sensing Domain Terminology Evaluation Runner.
Evaluates model accuracy on 12 essential remote-sensing terminology probes:
- SAR, VV, VH polarization, microwave backscatter
- Multispectral bands (B02/B03/B04/B08) and near-infrared reflectance
- NDVI (Normalized Difference Vegetation Index) calculation & vegetation vigor
- Built-up area / Urban fabric
- Water bodies and NIR absorption
- Agricultural land and complex cultivation patterns
- Cloud cover masking and cirrus band reflectance
- Spatial resolution and Ground Sampling Distance (GSD)
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List
import numpy as np
from PIL import Image

from evaluation.vrsbench.metrics import compute_exact_match, compute_token_f1


TERMINOLOGY_PROBES = [
    {
        "id": "term_01_sar_backscatter",
        "question": "What type of radar scattering mechanism characterizes calm water bodies in SAR imagery?",
        "reference": "Specular reflection resulting in very low radar backscatter.",
        "key_terms": ["specular", "backscatter", "low"],
        "scene_color": [20, 30, 80]  # dark blue / low reflection
    },
    {
        "id": "term_02_sar_polarization",
        "question": "Which dual-polarization channels are provided by Sentinel-1 in standard IW mode?",
        "reference": "VV and VH polarizations.",
        "key_terms": ["vv", "vh"],
        "scene_color": [50, 50, 50]
    },
    {
        "id": "term_03_multispectral_bands",
        "question": "Which Sentinel-2 spectral bands correspond to Blue, Green, Red, and NIR at 10m resolution?",
        "reference": "B02, B03, B04, and B08.",
        "key_terms": ["b02", "b03", "b04", "b08"],
        "scene_color": [40, 100, 40]
    },
    {
        "id": "term_04_ndvi_vegetation",
        "question": "What spectral index uses Red and NIR reflectance to quantify photosynthetic vegetation vigor?",
        "reference": "Normalized Difference Vegetation Index (NDVI).",
        "key_terms": ["ndvi", "normalized difference vegetation index"],
        "scene_color": [30, 140, 40]
    },
    {
        "id": "term_05_built_up_area",
        "question": "How is dense residential and commercial infrastructure classified in CORINE Land Cover nomenclature?",
        "reference": "Urban fabric and industrial or commercial units.",
        "key_terms": ["urban fabric", "industrial", "commercial"],
        "scene_color": [130, 130, 130]
    },
    {
        "id": "term_06_water_body_nir",
        "question": "Why do clear water bodies appear dark in near-infrared (NIR) satellite bands?",
        "reference": "Water bodies exhibit strong near-infrared absorption with minimal specular reflectance.",
        "key_terms": ["absorption", "near-infrared", "water"],
        "scene_color": [10, 20, 60]
    },
    {
        "id": "term_07_agricultural_land",
        "question": "What land cover class describes fragmented crop parcels and rural farming patterns in satellite scenes?",
        "reference": "Arable land and complex cultivation patterns.",
        "key_terms": ["arable land", "cultivation patterns"],
        "scene_color": [130, 115, 60]
    },
    {
        "id": "term_08_cloud_cover_masking",
        "question": "Which optical band is primarily used to detect high-altitude thin cirrus clouds in Sentinel-2?",
        "reference": "Band 10 (cirrus band) at 1.375 micrometers.",
        "key_terms": ["band 10", "cirrus"],
        "scene_color": [240, 240, 240]
    },
    {
        "id": "term_09_spatial_resolution_gsd",
        "question": "What is the ground sampling distance (GSD) of Sentinel-2 visible and NIR bands?",
        "reference": "10 meters spatial resolution per pixel.",
        "key_terms": ["10 meter", "10m", "ground sampling distance"],
        "scene_color": [60, 90, 60]
    },
    {
        "id": "term_10_sar_speckle",
        "question": "What granular interference phenomenon is inherent to coherent synthetic aperture radar imaging?",
        "reference": "Speckle noise requiring multi-looking or spatial filtering.",
        "key_terms": ["speckle", "noise"],
        "scene_color": [70, 70, 70]
    },
    {
        "id": "term_11_forest_canopy",
        "question": "How are dense woodland ecosystems categorized under standardized remote sensing taxonomy?",
        "reference": "Broad-leaved forest, coniferous forest, and mixed woodland.",
        "key_terms": ["forest", "broad-leaved", "coniferous"],
        "scene_color": [25, 95, 30]
    },
    {
        "id": "term_12_transitional_woodland",
        "question": "What class designates bushy or scrub vegetation between open grassland and closed canopy forest?",
        "reference": "Transitional woodland, shrub.",
        "key_terms": ["transitional woodland", "shrub"],
        "scene_color": [90, 110, 70]
    }
]


class DomainTerminologyRunner:
    """
    Evaluates vision-language models on controlled remote-sensing terminology probes.
    """

    def __init__(self, probes: List[Dict[str, Any]] = None):
        self.probes = probes or TERMINOLOGY_PROBES

    def evaluate(self, predict_fn: Callable[[Image.Image, str], str]) -> Dict[str, Any]:
        """
        Runs the model against all terminology probes and calculates accuracy, exact match, and token F1.
        """
        exact_matches = []
        token_f1s = []
        term_hits = []
        results = []

        for p in self.probes:
            # Create synthetic probe image patch corresponding to scene color
            color = p.get("scene_color", [100, 100, 100])
            img_arr = np.full((120, 120, 3), color, dtype=np.uint8)
            img = Image.fromarray(img_arr)

            pred = predict_fn(img, p["question"])

            em = compute_exact_match(pred, p["reference"])
            f1 = compute_token_f1(pred, p["reference"])

            # Check if domain key terms are present in prediction
            pred_low = pred.lower()
            hit_count = sum(1 for term in p["key_terms"] if term.lower() in pred_low)
            term_score = 1.0 if hit_count >= 1 else 0.0

            exact_matches.append(em)
            token_f1s.append(f1)
            term_hits.append(term_score)

            results.append({
                "id": p["id"],
                "question": p["question"],
                "reference": p["reference"],
                "prediction": pred,
                "exact_match": em,
                "token_f1": f1,
                "term_hit": term_score,
            })

        mean_em = float(np.mean(exact_matches))
        mean_f1 = float(np.mean(token_f1s))
        term_accuracy = float(np.mean(term_hits))

        return {
            "total_samples": len(self.probes),
            "exact_match": round(mean_em, 4),
            "token_f1": round(mean_f1, 4),
            "term_accuracy": round(term_accuracy, 4),
            "results": results,
        }

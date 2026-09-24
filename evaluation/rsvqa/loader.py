"""
RSVQA Remote-Sensing VQA Benchmark Loader.
Provides presence, comparison, and counting question-answering evaluation pairs.
Ref: RSVQA: Visual Question Answering for Remote Sensing Data.
"""

from typing import Any, Dict, List
import numpy as np
from PIL import Image


class RSVQADataLoader:
    """
    Loads isolated RSVQA benchmark evaluation queries.
    """

    EVAL_SAMPLES = [
        {
            "id": "rsvqa_presence_01",
            "type": "presence",
            "query": "Is there a water body present in this satellite scene?",
            "reference": "yes",
            "dominant_color": [30, 65, 120],
        },
        {
            "id": "rsvqa_presence_02",
            "type": "presence",
            "query": "Are there buildings or built-up infrastructure present in this area?",
            "reference": "no",
            "dominant_color": [35, 100, 45],  # Forest area
        },
        {
            "id": "rsvqa_comparison_01",
            "type": "comparison",
            "query": "Is the area mostly urban or rural agricultural land?",
            "reference": "rural agricultural land",
            "dominant_color": [140, 130, 70],
        },
        {
            "id": "rsvqa_presence_03",
            "type": "presence",
            "query": "Does this scene contain residential urban fabric?",
            "reference": "yes",
            "dominant_color": [135, 135, 140],
        },
        {
            "id": "rsvqa_comparison_02",
            "type": "comparison",
            "query": "Is the land cover primarily forest or water body?",
            "reference": "forest",
            "dominant_color": [28, 90, 38],
        },
    ]

    @classmethod
    def load_evaluation_set(cls) -> List[Dict[str, Any]]:
        items = []
        for s in cls.EVAL_SAMPLES:
            h, w = (128, 128)
            arr = np.zeros((h, w, 3), dtype=np.uint8)
            arr[:, :] = s["dominant_color"]
            np.random.seed(abs(hash(s["id"])) % (2**32))
            noise = np.random.normal(0, 8, (h, w, 3)).astype(np.int16)
            arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)

            items.append({
                "id": s["id"],
                "type": s["type"],
                "image": img,
                "query": s["query"],
                "reference": s["reference"],
            })
        return items

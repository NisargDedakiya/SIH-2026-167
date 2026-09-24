"""
Deterministic Dataset Splitter and Data Leakage Guard.
Enforces disjoint train/validation/test partitions with geographic grouping where available.
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class DatasetSplitter:
    """
    Splits dataset samples deterministically and verifies zero leakage across partitions.
    """

    @classmethod
    def split(
        cls,
        samples: List[Dict[str, Any]],
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
        group_by_prefix: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Splits sample list into train, val, and test subsets.
        If group_by_prefix is True, groups samples by tile identifier (e.g., 'S2A_MSIL2A_20170613T101031_N0205_R022_T32ULD')
        to prevent spatial correlation leakage between partitions.
        """
        assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Split ratios must sum to 1.0."

        rng = random.Random(seed)

        if group_by_prefix:
            # Group by Sentinel tile code if extractable from sample_id
            groups: Dict[str, List[Dict[str, Any]]] = {}
            for s in samples:
                sid = s.get("sample_id", "")
                parts = sid.split("_")
                # Sentinel-2 tile code is typically tile token like T32ULD or first 3 tokens
                group_key = parts[5] if len(parts) > 5 else (parts[0] if parts else "group_0")
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(s)

            group_keys = sorted(list(groups.keys()))
            rng.shuffle(group_keys)

            train_samples: List[Dict[str, Any]] = []
            val_samples: List[Dict[str, Any]] = []
            test_samples: List[Dict[str, Any]] = []

            total_samples = len(samples)
            target_train = int(total_samples * train_ratio)
            target_val = int(total_samples * val_ratio)

            for gk in group_keys:
                grp = groups[gk]
                if len(train_samples) < target_train:
                    train_samples.extend(grp)
                elif len(val_samples) < target_val:
                    val_samples.extend(grp)
                else:
                    test_samples.extend(grp)

            # Fallback if uneven grouping produced empty sets
            if not val_samples and len(train_samples) > 2:
                val_samples.append(train_samples.pop())
            if not test_samples and len(train_samples) > 2:
                test_samples.append(train_samples.pop())

        else:
            shuffled = list(samples)
            rng.shuffle(shuffled)
            n_total = len(shuffled)
            n_train = int(n_total * train_ratio)
            n_val = int(n_total * val_ratio)

            train_samples = shuffled[:n_train]
            val_samples = shuffled[n_train:n_train + n_val]
            test_samples = shuffled[n_train + n_val:]

        # Strict Data Leakage Assertion
        cls.verify_zero_leakage(train_samples, val_samples, test_samples)

        return {
            "train": train_samples,
            "validation": val_samples,
            "test": test_samples,
            "metadata": {
                "seed": seed,
                "train_count": len(train_samples),
                "val_count": len(val_samples),
                "test_count": len(test_samples),
                "grouped_by_prefix": group_by_prefix,
            }
        }

    @classmethod
    def verify_zero_leakage(
        cls,
        train: List[Dict[str, Any]],
        val: List[Dict[str, Any]],
        test: List[Dict[str, Any]]
    ) -> None:
        """
        Raises ValueError if any sample_id is shared across partitions.
        """
        train_ids: Set[str] = {s["sample_id"] for s in train}
        val_ids: Set[str] = {s["sample_id"] for s in val}
        test_ids: Set[str] = {s["sample_id"] for s in test}

        tv_leak = train_ids.intersection(val_ids)
        tt_leak = train_ids.intersection(test_ids)
        vt_leak = val_ids.intersection(test_ids)

        if tv_leak:
            raise ValueError(f"CRITICAL: Data leakage detected between train and validation: {tv_leak}")
        if tt_leak:
            raise ValueError(f"CRITICAL: Data leakage detected between train and test: {tt_leak}")
        if vt_leak:
            raise ValueError(f"CRITICAL: Data leakage detected between validation and test: {vt_leak}")

    @classmethod
    def save_splits(cls, splits: Dict[str, Any], output_dir: str | Path) -> None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for key in ["train", "validation", "test"]:
            if key in splits:
                with open(out / f"{key}.json", "w", encoding="utf-8") as f:
                    json.dump(splits[key], f, indent=2)
        if "metadata" in splits:
            with open(out / "splits_metadata.json", "w", encoding="utf-8") as f:
                json.dump(splits["metadata"], f, indent=2)

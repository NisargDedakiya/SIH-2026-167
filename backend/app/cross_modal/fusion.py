"""
Cross-Modal Fusion Strategy & Modality Dynamics for Optical and SAR Imagery.
Implements Stage B: Joint Feature Representation, Modality Contribution Profiling,
and Explicit Modality Disagreement Analysis.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.cross_modal.models import (
    DISAGREEMENT_AGREEMENT,
    DISAGREEMENT_DISAGREEMENT,
    DISAGREEMENT_INSUFFICIENT,
    DISAGREEMENT_PARTIAL,
)
from app.cross_modal.schemas import ModalityContribution, ModalityDisagreement


class CrossModalFusion:
    """
    Combines optical spectral representations and SAR backscatter representations.
    Analyzes modality-specific contributions and identifies agreements/divergences.
    """

    @classmethod
    def fuse_representations(
        cls,
        optical_features: np.ndarray,
        sar_features: np.ndarray,
        strategy: str = "feature_fusion",
        weights: Optional[Tuple[float, float]] = None,
    ) -> np.ndarray:
        """
        Stage B: Merges optical features and SAR features into a joint representation tensor.
        Optical: captures spectral reflectivity, vegetative pigmentation, optical textures.
        SAR: captures radar surface roughness, dielectric permittivity, volumetric canopy scattering.
        """
        w_opt, w_sar = weights if weights else (0.5, 0.5)

        # Ensure matching spatial dimensions
        h1, w1 = optical_features.shape[:2]
        h2, w2 = sar_features.shape[:2]

        if (h1, w1) != (h2, w2):
            raise ValueError(f"Feature spatial dimensions mismatch: optical ({h1}x{w1}) vs SAR ({h2}x{w2}).")

        if strategy == "feature_fusion" or strategy == "gated_fusion":
            # Normalize channels
            opt_norm = optical_features.astype(np.float32) / (np.max(optical_features) + 1e-6)
            sar_norm = sar_features.astype(np.float32) / (np.max(sar_features) + 1e-6)

            # If channel depths differ, concatenate along channel axis for full fidelity
            if opt_norm.ndim == 2:
                opt_norm = np.expand_dims(opt_norm, -1)
            if sar_norm.ndim == 2:
                sar_norm = np.expand_dims(sar_norm, -1)

            # Joint tensor concatenation
            joint_features = np.concatenate([opt_norm * w_opt, sar_norm * w_sar], axis=-1)
            return joint_features
        else:
            # Fallback concatenation
            return np.concatenate([optical_features, sar_features], axis=-1)

    @classmethod
    def evaluate_modality_contributions(
        cls,
        query: str,
        optical_sensor: Optional[str] = None,
        sar_sensor: Optional[str] = None,
        polarization: Optional[str] = None,
        has_clouds: bool = False,
    ) -> Tuple[ModalityContribution, ModalityContribution]:
        """
        Produces verifiable, structured modality contributions based on physical sensor characteristics.
        Never hallucinates arbitrary scientific interpretations.
        """
        q_lower = query.lower()
        pol_desc = f" ({polarization})" if polarization else ""

        if "water" in q_lower or "river" in q_lower or "lake" in q_lower:
            opt_contrib = "Visible spectral absorption in near-infrared and true-color aquatic boundaries."
            opt_features = ["spectral reflectance", "water coloration", "shallow shoreline discrimination"]
            sar_contrib = f"Specular radar reflection away from antenna causing pronounced low backscatter{pol_desc}."
            sar_features = ["smooth surface low backscatter", "sharp dielectric water-land boundary", "flood delineation"]

        elif "urban" in q_lower or "building" in q_lower or "structure" in q_lower or "infrastructure" in q_lower:
            opt_contrib = "Orthogonal rooftop geometric outlines, road asphalt contrast, and visual textures."
            opt_features = ["geometric roof footprints", "road network spectral contrast", "visual land use"]
            sar_contrib = f"Strong double-bounce corner reflection from vertical building-ground orthogonal surfaces{pol_desc}."
            sar_features = ["double-bounce corner scattering", "metallic/dielectric bright returns", "structural density"]

        elif "vegetation" in q_lower or "agriculture" in q_lower or "crop" in q_lower or "forest" in q_lower:
            opt_contrib = "Chlorophyll absorption and spectral greenness / NDVI signature."
            opt_features = ["chlorophyll spectral absorption", "crop canopy color variation", "field boundary lines"]
            sar_contrib = f"Volumetric depolarizing backscatter from vegetation crown/canopy roughness{pol_desc}."
            sar_features = ["volume scattering from biomass", "soil moisture dielectric response", "surface roughness"]

        elif "sar reveal" in q_lower or "does not" in q_lower or "difficult to see" in q_lower:
            opt_contrib = "Surface-level visual appearance subject to atmospheric scattering, lighting, and cloud cover."
            opt_features = ["visual color appearance", "solar shadow angles", "surface albedo"]
            sar_contrib = f"Active microwave surface roughness and dielectric sensitivity independent of sunlight/clouds{pol_desc}."
            sar_features = ["microwave dielectric penetration", "orthogonal corner reflections", "roughness discrimination"]

        else:
            opt_contrib = "Multi-band visual spectral textures, surface color variation, and optical contrast."
            opt_features = ["multi-spectral reflectivity", "visual land cover", "edge contrast"]
            sar_contrib = f"Active radar backscatter intensity, surface roughness, and dielectric property distribution{pol_desc}."
            sar_features = ["backscatter intensity", "structural geometry", "surface roughness"]

        optical_summary = ModalityContribution(
            available=True,
            modality="optical",
            sensor=optical_sensor,
            contribution=opt_contrib,
            features=opt_features,
        )

        sar_summary = ModalityContribution(
            available=True,
            modality="sar",
            sensor=sar_sensor,
            contribution=sar_contrib,
            features=sar_features,
        )

        return optical_summary, sar_summary

    @classmethod
    def evaluate_disagreement(
        cls,
        query: str,
        optical_signal: Dict[str, Any],
        sar_signal: Dict[str, Any],
    ) -> ModalityDisagreement:
        """
        Stage C: Analyzes whether optical and SAR evidence agree or diverge.
        Explicitly represents:
        AGREEMENT, PARTIAL_AGREEMENT, DISAGREEMENT, INSUFFICIENT_EVIDENCE
        """
        opt_conf = optical_signal.get("confidence", 0.0)
        sar_conf = sar_signal.get("confidence", 0.0)
        opt_detected = optical_signal.get("detected", True)
        sar_detected = sar_signal.get("detected", True)

        if opt_conf < 0.30 and sar_conf < 0.30:
            return ModalityDisagreement(
                agreement_status=DISAGREEMENT_INSUFFICIENT,
                disagreement_type="LOW_CONFIDENCE",
                explanation="The optical and SAR evidence do not provide sufficiently consistent support for a single conclusion."
            )

        # Both agree on presence or feature
        if opt_detected and sar_detected:
            return ModalityDisagreement(
                agreement_status=DISAGREEMENT_AGREEMENT,
                disagreement_type=None,
                explanation="Both optical visual spectral evidence and SAR radar scattering corroborate the identified spatial features with concordant spatial boundaries."
            )

        # Divergence: One detects while the other does not (e.g. optical cloud cover or shadow)
        if opt_detected != sar_detected:
            q_lower = query.lower()
            if "cloud" in q_lower or optical_signal.get("cloud_obscured", False):
                return ModalityDisagreement(
                    agreement_status=DISAGREEMENT_PARTIAL,
                    disagreement_type="ATMOSPHERIC_OBSCURATION",
                    explanation="Optical imagery is partially obscured by atmospheric haze/cloud cover, whereas SAR microwave signals penetrate to reveal underlying ground structure."
                )
            elif "water" in q_lower:
                return ModalityDisagreement(
                    agreement_status=DISAGREEMENT_PARTIAL,
                    disagreement_type="SPECULAR_REFLECTION_CONTRAST",
                    explanation="Modality divergence observed: SAR exhibits pronounced specular null backscatter characteristic of smooth water surfaces while optical shows spectral absorption."
                )
            else:
                return ModalityDisagreement(
                    agreement_status=DISAGREEMENT_DISAGREEMENT,
                    disagreement_type="CROSS_MODAL_SIGNAL_DIVERGENCE",
                    explanation="Optical and SAR modalities exhibit conflicting evidence: target structure is supported by one sensor but lacks corresponding backscatter or spectral verification in the other."
                )

        return ModalityDisagreement(
            agreement_status=DISAGREEMENT_AGREEMENT,
            disagreement_type=None,
            explanation="Optical and SAR sensor observations are in mutual agreement regarding target scene characteristics."
        )

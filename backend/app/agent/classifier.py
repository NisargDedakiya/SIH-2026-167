"""
Query Normalization and Hybrid Intent Classification for SatQuery AI.
Combines deterministic heuristic pattern matching, image context constraints,
and ambiguity detection into an auditable classification decision.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ClassificationResult:
    original_query: str
    normalized_query: str
    intent: str
    confidence: float
    reasoning_summary: str
    is_ambiguous: bool = False
    clarification_prompt: Optional[str] = None


class QueryNormalizer:
    """Normalizes formatting noise and whitespace while preserving semantic query tokens."""

    @staticmethod
    def normalize(query: str) -> str:
        if not query:
            return ""
        # 1. Normalize line breaks and tabs to spaces
        text = re.sub(r"[\r\n\t]+", " ", query)
        # 2. Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)
        # 3. Strip leading and trailing whitespace
        text = text.strip()
        return text


class QueryClassifier:
    """
    Hybrid Query Intent Classifier.
    Evaluates lexical patterns, question syntax, spatial/temporal triggers,
    and input context (image count, modality) to determine target task.
    """

    # Keyword rules for Phase 3 and future tasks
    CROSS_MODAL_TRIGGERS = [
        "optical and sar",
        "sar and optical",
        "compare optical and sar",
        "optical/sar",
        "fuse sar",
        "combine sar",
        "multimodal",
        "cross-modal",
        "cross modal",
        "radar and optical",
        "optical and radar",
        "both images",
        "both modalities",
        "sar reveal",
        "sar show",
        "in the sar",
        "sar image",
        "cartosat and risat",
        "risat and cartosat",
        "complementary information from optical and sar",
        "supported by both",
        "difficult to see in the optical",
    ]

    CHANGE_ANALYSIS_TRIGGERS = [
        "what changed",
        "which areas changed",
        "what areas changed",
        "which regions changed",
        "changed",
        "change between",
        "changes between",
        "difference between",
        "two dates",
        "two images",
        "before and after",
        "temporal difference",
        "from last year",
        "over time",
        "compare this image with",
        "compare these two",
        "construction occur",
        "built-up area increase",
        "built up area increase",
        "vegetation decrease",
        "new roads",
        "new structures",
        "new buildings",
        "water body change",
        "major changes",
        "more urban development",
        "urban development in the second",
        "where did construction",
    ]

    GROUNDING_TRIGGERS = [
        "highlight",
        "locate",
        "outline",
        "bound",
        "bounding box",
        "detect and locate",
        "pinpoint",
        "segment",
        "where is the",
        "where are the",
        "draw a box",
        "show me where",
    ]

    CAPTION_TRIGGERS = [
        "describe",
        "description",
        "caption",
        "overview",
        "summarize",
        "summary of this scene",
        "what does this scene contain",
        "tell me the story",
        "scene description",
        "brief description",
        "give an overview",
    ]

    VQA_TRIGGERS = [
        "what type of",
        "what is",
        "what are",
        "how many",
        "is there",
        "are there",
        "which",
        "why",
        "does this",
        "can you see",
        "identify the",
        "count the",
        "classify the",
    ]

    # Ambiguous phrases that lack specific intent
    AMBIGUOUS_PATTERNS = [
        r"^tell me about this\.?$",
        r"^tell me about it\.?$",
        r"^what is this\.?$",
        r"^explain this\.?$",
        r"^analyze this\.?$",
        r"^inspect this\.?$",
        r"^info\.?$",
        r"^hello\.?$",
        r"^help\.?$",
    ]

    @classmethod
    def classify(
        cls,
        query: str,
        input_context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Executes 4-stage hybrid classification:
        Stage 1: Query normalization.
        Stage 2: Input context analysis (image count, modality).
        Stage 3: Ambiguity detection.
        Stage 4: Pattern & heuristic evaluation.
        """
        original = query
        normalized = QueryNormalizer.normalize(query)
        lower_q = normalized.lower()
        context = input_context or {}
        num_images = context.get("number_of_images", 1)

        # Stage 1: Empty check
        if not normalized:
            return ClassificationResult(
                original_query=original,
                normalized_query=normalized,
                intent="UNKNOWN",
                confidence=0.0,
                reasoning_summary="Empty query provided.",
                is_ambiguous=True,
                clarification_prompt="Please provide a question or instruction about the satellite image."
            )

        # Stage 2: Ambiguity detection
        for pattern in cls.AMBIGUOUS_PATTERNS:
            if re.match(pattern, lower_q):
                return ClassificationResult(
                    original_query=original,
                    normalized_query=normalized,
                    intent="AMBIGUOUS",
                    confidence=0.40,
                    reasoning_summary="Query expresses broad interest without specifying whether a general scene summary or specific question answer is desired.",
                    is_ambiguous=True,
                    clarification_prompt="Would you like a scene description or an answer to a specific question?"
                )

        # Stage 3: Multi-modal / Cross-modal triggers & context evaluation
        modalities = [str(m).lower() for m in context.get("modalities", [])]
        has_optical = any(m in ["optical", "multispectral"] for m in modalities)
        has_sar = any(m in ["sar", "radar"] for m in modalities)
        is_cross_modal_context = (
            context.get("pair_type") == "cross_modal"
            or context.get("cross_modal_pair_id") is not None
            or (has_optical and has_sar)
        )

        for trigger in cls.CROSS_MODAL_TRIGGERS:
            if trigger in lower_q:
                return ClassificationResult(
                    original_query=original,
                    normalized_query=normalized,
                    intent="CROSS_MODAL_ANALYSIS",
                    confidence=0.95,
                    reasoning_summary=f"Matched multi-modal cross-sensor trigger: '{trigger}'."
                )

        if is_cross_modal_context:
            return ClassificationResult(
                original_query=original,
                normalized_query=normalized,
                intent="CROSS_MODAL_ANALYSIS",
                confidence=0.96,
                reasoning_summary="Input context explicitly pairs Optical/Multispectral and SAR sensor modalities."
            )

        # Stage 4: Bi-temporal / Change Analysis triggers
        for trigger in cls.CHANGE_ANALYSIS_TRIGGERS:
            if trigger in lower_q or (num_images > 1 and "differ" in lower_q):
                return ClassificationResult(
                    original_query=original,
                    normalized_query=normalized,
                    intent="CHANGE_ANALYSIS",
                    confidence=0.94,
                    reasoning_summary=f"Matched temporal change analysis trigger: '{trigger}'."
                )

        # Stage 5: Grounding triggers
        for trigger in cls.GROUNDING_TRIGGERS:
            if lower_q.startswith(trigger) or f" {trigger} " in f" {lower_q} ":
                return ClassificationResult(
                    original_query=original,
                    normalized_query=normalized,
                    intent="GROUNDING",
                    confidence=0.90,
                    reasoning_summary=f"Matched spatial grounding / localization directive: '{trigger}'."
                )

        # Stage 6: Scene description triggers
        for trigger in cls.CAPTION_TRIGGERS:
            if trigger in lower_q:
                return ClassificationResult(
                    original_query=original,
                    normalized_query=normalized,
                    intent="SCENE_DESCRIPTION",
                    confidence=0.95,
                    reasoning_summary=f"Matched scene captioning instruction: '{trigger}'."
                )

        # Stage 7: Visual Question Answering (VQA) triggers or interrogative syntax
        for trigger in cls.VQA_TRIGGERS:
            if trigger in lower_q:
                return ClassificationResult(
                    original_query=original,
                    normalized_query=normalized,
                    intent="VISUAL_QUESTION_ANSWERING",
                    confidence=0.93,
                    reasoning_summary=f"Matched visual question query pattern: '{trigger}'."
                )

        # Interrogative check: ends with question mark or starts with wh- word
        if lower_q.endswith("?") or any(lower_q.startswith(w) for w in ["what", "where", "how", "who", "which", "is", "are", "can"]):
            return ClassificationResult(
                original_query=original,
                normalized_query=normalized,
                intent="VISUAL_QUESTION_ANSWERING",
                confidence=0.88,
                reasoning_summary="Interrogative structure detected targeting visual information."
            )

        # Default fallback to scene description if imperative/declarative noun phrase, or ambiguous
        if len(lower_q.split()) <= 2:
            return ClassificationResult(
                original_query=original,
                normalized_query=normalized,
                intent="AMBIGUOUS",
                confidence=0.50,
                reasoning_summary="Short phrase with ambiguous intent.",
                is_ambiguous=True,
                clarification_prompt="Would you like a scene description or an answer to a specific question?"
            )

        # Default to VQA for general analytical inquiries
        return ClassificationResult(
            original_query=original,
            normalized_query=normalized,
            intent="VISUAL_QUESTION_ANSWERING",
            confidence=0.75,
            reasoning_summary="Defaulted to visual query answering based on general analytical context."
        )

"""
Remote-Sensing Vision-Language Text and Prompt Preprocessor.
Standardizes instruction prompts and answers for RS VQA and captioning.
"""

import re
from typing import Dict, List, Optional


class RSTextPreprocessor:
    """
    Cleans, grounds, and tokenizes remote-sensing queries and target descriptions.
    """

    PROMPT_PREFIX = "Satellite image analysis: "

    @classmethod
    def format_query(cls, raw_query: str) -> str:
        """
        Formats user query with remote-sensing prompt framing.
        """
        cleaned = raw_query.strip()
        if not cleaned.endswith(("?", ".")):
            cleaned += "?"
        return f"{cls.PROMPT_PREFIX}{cleaned}"

    @staticmethod
    def normalize_answer(raw_answer: str) -> str:
        """
        Normalizes target answer for exact match and token metric comparisons.
        """
        text = raw_answer.lower().strip()
        # Remove extra whitespace and trailing punctuation
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[.,;!]+$", "", text)
        return text

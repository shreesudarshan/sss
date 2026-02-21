"""Text normalization helpers for blind-index token generation."""

import re


def normalize_string(text: str) -> str:
    """Normalize input before trigram extraction."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def generate_trigrams(text: str) -> list[str]:
    """Generate unique 3-character windows, replacing spaces with underscores."""
    normalized = normalize_string(text)
    if len(normalized) < 3:
        return []

    trigrams = []
    for i in range(len(normalized) - 2):
        trigram = normalized[i : i + 3].replace(" ", "_")
        if len(trigram) == 3:
            trigrams.append(trigram)

    return list(set(trigrams))

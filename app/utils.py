import re
from typing import List

def normalize_string(text: str) -> str:
    """
    Normalize string for tokenization:
    - lowercase
    - strip whitespace
    - remove non-alphanumeric except spaces
    - collapse multiple spaces
    """
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def generate_trigrams(text: str) -> List[str]:
    """
    Generate sliding window trigrams from normalized text.
    
    "john doe" -> ['joh', 'ohn', 'n d', ' do', 'doe']
    """
    normalized = normalize_string(text)
    if len(normalized) < 3:
        return []
    
    trigrams = []
    for i in range(len(normalized) - 2):
        trigram = normalized[i:i+3].replace(' ', '_')  # Use _ for spaces
        if len(trigram) == 3:
            trigrams.append(trigram)
    
    return list(set(trigrams))  # Deduplicate

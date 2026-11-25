"""Sentence-aware chunks with approximate word limits and source spans."""
import re
from collections import Counter


def boilerplate(documents):
    counts = Counter()
    for rows in documents.values():
        counts.update({s.casefold() for text, _ in rows for s in sentences(text)})
    return {s for s, n in counts.items() if n >= 4}


def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]


def chunk(rows, ignored=(), size=140, overlap=25):
    # Each word carries its own source location, preserving video/page boundaries.
    words = []
    locations = []
    for text, loc in rows:
        for sentence in sentences(text):
            if sentence.casefold() in ignored:
                continue
            tokens = sentence.split()
            words.extend(tokens)
            locations.extend([loc] * len(tokens))
    result = []
    for start in range(0, len(words), size - overlap):
        end = min(start + size, len(words))
        unique = []
        for loc in locations[start:end]:
            if loc not in unique:
                unique.append(loc)
        result.append({'text': ' '.join(words[start:end]), 'start': start, 'end': end, 'location': unique})
        if end == len(words):
            break
    return result

"""Reproducible, uncalibrated mock signal; not evidence of AI authorship."""
import re
import statistics


def estimate(text):
    lengths = [len(s.split()) for s in re.split(r'[.!?]+', text) if s.strip()]
    if len(lengths) < 3:
        return None
    cv = statistics.pstdev(lengths) / max(statistics.mean(lengths), 1)
    return round(100 / (1 + 3 * cv), 2)

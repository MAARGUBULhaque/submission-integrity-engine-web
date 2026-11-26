"""Extract text from PDF documents and external reference files."""

from pathlib import Path
import re
import fitz


def extract(path):
    path = Path(path)

    if not path.stat().st_size:
        raise ValueError("Empty file")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        with fitz.open(path) as doc:
            rows = [
                (page.get_text(), {"page": i + 1})
                for i, page in enumerate(doc)
            ]

    elif suffix == ".txt":
        rows = [
            (path.read_text(encoding="utf-8"), {"line": 1})
        ]

    else:
        raise ValueError("Unsupported file format")

    rows = [
        (re.sub(r"\s+", " ", text).strip(), location)
        for text, location in rows
        if text.strip()
    ]

    if not rows:
        raise ValueError("No readable text found")

    return rows

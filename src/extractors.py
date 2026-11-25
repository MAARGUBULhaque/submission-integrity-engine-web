"""Extract text with source coordinates. DOCX uses paragraph IDs, not guessed pages."""
from pathlib import Path
import re
import subprocess
import fitz
from docx import Document


def extract(path, whisper_model=None):
    path = Path(path)
    if not path.stat().st_size:
        raise ValueError('Empty file')
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        with fitz.open(path) as doc:
            rows = [(p.get_text(), {'page': i + 1}) for i, p in enumerate(doc)]
    elif suffix == '.docx':
        rows = [(p.text, {'paragraph': i + 1}) for i, p in enumerate(Document(path).paragraphs)]
    elif suffix == '.mp4':
        if whisper_model is None:
            raise ValueError('Whisper unavailable or disabled')
        probe = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-f', 'null', '-'], capture_output=True)
        if probe.returncode:
            raise ValueError('No readable audio track')
        result = whisper_model.transcribe(str(path), language='en', fp16=False)
        rows = [(s['text'], {'timestamp': [round(s['start'], 2), round(s['end'], 2)]}) for s in result['segments'] if s.get('no_speech_prob', 0) < .6]
    elif suffix == '.txt':
        rows = [(path.read_text(encoding='utf-8'), {'line': 1})]
    else:
        raise ValueError('Unsupported format')
    rows = [(re.sub(r'\s+', ' ', t).strip(), loc) for t, loc in rows if t.strip()]
    if not rows:
        raise ValueError('No readable text or speech')
    return rows

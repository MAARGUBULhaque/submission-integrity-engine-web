import argparse
import csv
import json
import logging
from pathlib import Path
from src.extractors import extract
from src.chunking import boilerplate, chunk
from src.embeddings import Encoder, VectorIndex
from src.ai_detector import estimate
from src.reporter import write_report


def coverage(chunks, matched):
    covered = {i for c in matched for i in range(c['start'], c['end'])}
    total = max((c['end'] for c in chunks), default=0)
    return round(100 * len(covered) / total, 2) if total else None


def run(input_dir, output_dir, reference_dir, backend='semantic', threshold=.8, skip_video=False):
    output_dir.mkdir(parents=True, exist_ok=True)
    docs, errors = {}, {}
    files = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in ('.pdf', '.docx', '.mp4'))
    model = None
    if not skip_video and any(p.suffix.lower() == '.mp4' for p in files):
        import whisper
        model = whisper.load_model('tiny')
    for p in files:
        try:
            docs[p.name] = extract(p, model)
        except Exception as exc:
            errors[p.name] = str(exc)
            logging.warning('%s: %s', p.name, exc)
    ignored = boilerplate(docs)
    chunks = {name: chunk(rows, ignored) for name, rows in docs.items()}
    encoder = Encoder(backend)
    peer = VectorIndex([(n, c) for n, cs in chunks.items() for c in cs], encoder)
    refs = []
    for p in sorted(reference_dir.glob('*.txt')):
        try:
            refs.extend((p.name, c) for c in chunk(extract(p)))
        except Exception as exc:
            logging.warning('Reference %s: %s', p, exc)
    external = VectorIndex(refs, encoder)
    matrix = {p.name: {q.name: None if p.name == q.name or p.name in errors or q.name in errors else 0.0 for q in files} for p in files}
    summary = []
    for p in files:
        name = p.name
        report = {'document_id': name, 'status': 'skipped' if name in errors else 'ok', 'total_integrity_risk': 'UNKNOWN', 'scores': {'peer_similarity_percentage': None, 'external_similarity_percentage': None, 'ai_generated_probability': None}, 'peer_matches': [], 'multimodal_matches': [], 'external_matches': [], 'explanations': errors.get(name, ''), 'backend': backend}
        if name not in errors:
            cs = chunks[name]
            matched_peer, matched_ext = [], []
            for c, v in zip(cs, encoder.encode([c['text'] for c in cs]) if cs else []):
                for index, is_peer in ((peer, True), (external, False)):
                    for other, source, score in index.search(v, name if is_peer else None, threshold):
                        match = {'matched_file': other, 'similarity_score': round(score, 4), 'query_passage': c['text'], 'matched_passage': source['text'], 'location': {'query': c['location'], 'matched': source['location']}}
                        group = ('multimodal_matches' if (p.suffix.lower() == '.mp4') != other.lower().endswith('.mp4') else 'peer_matches') if is_peer else 'external_matches'
                        report[group].append(match)
                        (matched_peer if is_peer else matched_ext).append(c)
                        if is_peer:
                            matrix[name][other] = max(matrix[name][other], score)
            ps, es = coverage(cs, matched_peer), coverage(cs, matched_ext) if refs else None
            ai = estimate(' '.join(t for t, _ in docs[name]))
            report['scores'] = dict(peer_similarity_percentage=ps, external_similarity_percentage=es, ai_generated_probability=ai)
            risk = max([s for s in (ps, es) if s is not None], default=-1)
            report['total_integrity_risk'] = 'HIGH' if risk >= 60 else 'MEDIUM' if risk >= 20 else 'LOW' if risk >= 0 else 'UNKNOWN'
            report['explanations'] = f'Flagged unique-word coverage at cosine threshold {threshold}; {len(ignored)} common sentences excluded corpus-wide. AI score is an uncalibrated mock and is not used for risk. Human review required.'
        write_report(report, output_dir)
        summary.append({k: report[k] for k in ('document_id', 'status', 'scores', 'total_integrity_risk')})
    (output_dir / 'summary.json').write_text(json.dumps(summary, indent=2))
    with (output_dir / 'summary_matrix.csv').open('w', newline='') as f:
        writer = csv.writer(f); names = list(matrix); writer.writerow(['document'] + names)
        for n in names:
            writer.writerow([n] + [matrix[n][q] for q in names])
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multimodal submission integrity prototype')
    parser.add_argument('--input_dir', type=Path, default=Path('sample_submissions'))
    parser.add_argument('--output_dir', type=Path, default=Path('reports'))
    parser.add_argument('--reference_dir', type=Path, default=Path('reference_data'))
    parser.add_argument('--backend', choices=['semantic', 'lexical'], default='semantic')
    parser.add_argument('--threshold', type=float, default=.70)
    parser.add_argument('--skip-video', action='store_true')
    args = parser.parse_args()
    if not 0 <= args.threshold <= 1:
        parser.error('threshold must be in [0, 1]')
    logging.basicConfig(level=logging.INFO)
    run(args.input_dir, args.output_dir, args.reference_dir, args.backend, args.threshold, args.skip_video)

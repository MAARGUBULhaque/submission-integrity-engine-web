import json


def write_report(report, output):
    name = report['document_id']
    (output / (name + '.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    lines = [f'# {name}', f"Status: {report['status']}", f"Risk: {report['total_integrity_risk']}", '', report['explanations'], '', '## Scores']
    lines.extend(f'- {key}: {value}' for key, value in report['scores'].items())
    for group in ('peer_matches', 'multimodal_matches', 'external_matches'):
        lines.append(f'\n## {group}')
        for m in report[group]:
            lines.extend([f"\n### {m['matched_file']} — {m['similarity_score']:.3f}", f"Query location: {m['location']['query']}", f"Source location: {m['location']['matched']}", f"\nQuery: {m['query_passage']}", f"\nSource: {m['matched_passage']}"])
    (output / (name + '.md')).write_text('\n'.join(lines), encoding='utf-8')

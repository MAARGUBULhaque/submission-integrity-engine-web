import argparse
import itertools
import json
from pathlib import Path
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score


def evaluate(reports, manifest):
    truth = json.loads(manifest.read_text())
    data = json.loads((reports / 'summary.json').read_text())
    valid = sorted(r['document_id'] for r in data if r['status'] == 'ok')
    positives = {frozenset(p) for p in truth['peer_positive_pairs']}
    expected, predicted, misses = [], [], []
    matches = {}
    for n in valid:
        r = json.loads((reports / (n + '.json')).read_text())
        matches[n] = {m['matched_file'] for m in r['peer_matches'] + r['multimodal_matches']}
    for a, b in itertools.combinations(valid, 2):
        y = frozenset((a,b)) in positives
        p = b in matches[a] or a in matches[b]
        expected.append(y); predicted.append(p)
        if y != p:
            misses.append({'pair': [a,b], 'expected': y, 'predicted': p})
    return {'valid_documents': len(valid), 'evaluated_pairs': len(expected), 'excluded_documents': [r['document_id'] for r in data if r['status'] != 'ok'], 'confusion_matrix_TN_FP_FN_TP': confusion_matrix(expected,predicted,labels=[False,True]).ravel().tolist(), 'precision': precision_score(expected,predicted,zero_division=0), 'recall': recall_score(expected,predicted,zero_division=0), 'f1': f1_score(expected,predicted,zero_division=0), 'mismatches': misses}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--reports',type=Path,default=Path('reports')); p.add_argument('--manifest',type=Path,default=Path('sample_submissions/dataset_manifest.json')); a=p.parse_args()
    result=evaluate(a.reports,a.manifest); (a.reports/'evaluation.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))

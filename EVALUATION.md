# PDF Plagiarism Detection Evaluation

## Evaluation Overview

The PDF-only plagiarism detection engine was evaluated
using a synthetic dataset containing 10 PDF submissions.

## Configuration

- Model: all-MiniLM-L6-v2
- Embedding dimensions: 384
- Similarity metric: Cosine similarity
- Similarity threshold: 0.70
- Inference device: CPU
- Evaluation type: Pairwise peer matching

## Dataset

| Parameter | Result |
|---|---:|
| Total submissions | 10 |
| Valid submissions | 9 |
| Skipped submissions | 1 |
| Evaluated pairs | 36 |
| Positive pairs | 2 |
| Negative pairs | 34 |

## Confusion Matrix

| Metric | Count |
|---|---:|
| True Positive | 2 |
| True Negative | 34 |
| False Positive | 0 |
| False Negative | 0 |

## Performance Metrics

| Metric | Result |
|---|---:|
| Accuracy | 100% |
| Precision | 100% |
| Recall | 100% |
| F1 Score | 100% |

## Browser Application Results

- Total PDF submissions: 10
- Successfully processed: 9
- High-risk submissions: 5
- Low-risk submissions: 4
- Skipped submissions: 1

The external reference matching case was also
successfully detected in the browser demonstration.

## Limitations

The evaluation uses a small synthetic development dataset.
These results do not establish real-world accuracy or
generalization to unseen documents.

The AI-generated content indicator is an unvalidated
statistical heuristic and is not used for risk classification.

Similarity scores require human verification.

## Conclusion

The PDF-only prototype successfully demonstrated exact
duplication detection, semantic paraphrase detection,
external reference matching and invalid file handling.

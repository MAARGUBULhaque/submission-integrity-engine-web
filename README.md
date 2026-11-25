# Multimodal Submission Integrity & Plagiarism Detection Engine

## Overview

A Python-based AI/ML pipeline designed to detect submission similarities across PDF documents, DOCX files, and MP4 videos.

The system uses semantic vector embeddings, cosine similarity, and automatic speech recognition to identify exact duplication, paraphrased content, cross-modal similarities, and external reference matches.

Developed for the Unstop AI/ML Engineer Assessment.

## Key Features

- Multimodal text extraction from PDF, DOCX, and MP4.
- Automatic speech recognition using Whisper Tiny.
- Semantic embeddings using all-MiniLM-L6-v2.
- NumPy-based vector similarity search.
- Internal peer-to-peer plagiarism detection.
- External reference similarity detection.
- AI-generated content estimation using a documented mock heuristic.
- Common boilerplate detection and exclusion.
- Self-match exclusion.
- Graceful handling of corrupted and empty files.
- Explainable reports containing matched passages, page numbers, paragraph numbers, and video timestamps.
- JSON, Markdown, and CSV report generation.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Core programming language |
| PyTorch | Model inference |
| PyMuPDF | PDF text extraction |
| python-docx | DOCX text extraction |
| FFmpeg | Audio extraction |
| OpenAI Whisper Tiny | Speech recognition |
| Sentence Transformers | Semantic embeddings |
| all-MiniLM-L6-v2 | Embedding model |
| NumPy | Vector indexing and cosine similarity |
| Scikit-learn | Evaluation utilities |
| Pytest | Automated testing |

## System Architecture

```text
PDF / DOCX / MP4
        |
Text Extraction / Speech Recognition
        |
Text Normalization
        |
Common Boilerplate Filtering
        |
Text Chunking and Metadata Preservation
        |
Semantic Vector Embeddings
        |
NumPy Cosine Similarity Search
        |
Peer Matching / External Matching
        |
Integrity Scoring + Independent AI Indicator
        |
Explainable JSON / Markdown / CSV Reports
```

## Installation

### Prerequisites

- Python 3.10 or 3.11 recommended.
- FFmpeg available in the system PATH.
- Internet access for the initial pretrained model downloads.

### Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Standard Installation

```bash
python -m pip install -r requirements.txt
```

### Intel macOS Compatibility

The project was successfully tested on an Intel MacBook Air running Python 3.11.3.

A dependency snapshot is provided in `requirements-macos-intel.txt`.

Older versions of PyTorch, NumPy, Numba, llvmlite, and PyMuPDF were required for compatibility.

```bash
python -m pip install "setuptools==75.8.2" wheel
python -m pip install --no-build-isolation -r requirements-macos-intel.txt
```

If Homebrew or FFmpeg is unavailable, configure the FFmpeg executable supplied by imageio-ffmpeg:

```bash
ln -sf "$(python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" "$VIRTUAL_ENV/bin/ffmpeg"
```

The pinned environment reflects the tested installation but has not been independently reproduced from a clean environment. Older dependencies should be used with synthetic assessment data only.

## Running the Pipeline

Execute the following command from the project root:

```bash
python run_integrity_check.py --input_dir ./sample_submissions --output_dir ./reports
```

The default cosine similarity threshold is 0.70.

To specify a custom threshold:

```bash
python run_integrity_check.py --input_dir ./sample_submissions --output_dir ./reports --threshold 0.75
```

The pretrained models are downloaded automatically during the first execution.

## Evaluation

```bash
python evaluate.py --reports ./reports
```

## Automated Tests

```bash
python -m pytest -q
```

## Dataset

The synthetic dataset consists of 13 submissions:

- 5 PDF files.
- 5 DOCX files.
- 3 MP4 files.

It includes exact duplication, paraphrased text, cross-modal duplication, external reference copying, AI-generated text, independent submissions, common boilerplate, an empty PDF, and a silent video.

Ground-truth relationships are documented in `sample_submissions/dataset_manifest.json`.

No private student submissions are used.

## Methodology

### 1. Multimodal Ingestion

PDF and DOCX documents are converted into text using dedicated extraction libraries.

MP4 audio is processed using FFmpeg and transcribed using Whisper Tiny. Source metadata is preserved for explainability.

### 2. Text Normalization and Chunking

Extracted content is normalized and divided into overlapping chunks. Repeated common sentences are excluded to reduce false positives.

### 3. Semantic Embeddings

The all-MiniLM-L6-v2 model converts text chunks into 384-dimensional vector representations.

### 4. Similarity Search

Normalized vector embeddings are compared using NumPy-based cosine similarity.

Self-matches are excluded, and matching chunks are flagged when their similarity exceeds the configured threshold.

Document-level similarity represents flagged unique-word coverage rather than a definitive percentage of plagiarized content.

### 5. External Reference Detection

Submission embeddings are compared against a local reference knowledge base.

This approach avoids commercial API costs and external search rate limits.

### 6. AI Content Estimation

The AI estimation module uses a reproducible, uncalibrated statistical mock heuristic.

Its output is not a reliable probability of AI authorship and is excluded from the overall plagiarism risk calculation.

### 7. Explainability

Generated reports include matched passages, source filenames, cosine similarity scores, PDF page references, DOCX paragraph references, and video timestamps.

All flagged content requires human verification.

## Evaluation Results

| Metric | Result |
|---|---|
| Total submissions | 13 |
| Valid submissions | 11 |
| Excluded submissions | 2 |
| Evaluated document pairs | 55 |
| True positives | 4 |
| True negatives | 51 |
| False positives | 0 |
| False negatives | 0 |
| Precision | 100% |
| Recall | 100% |
| F1 score | 100% |
| Automated tests | 6/6 passed |

### Threshold Optimization

| Threshold | Precision | Recall | F1 Score |
|---|---|---|---|
| 0.80 | 100% | 75% | 85.71% |
| 0.75 | 100% | 75% | 85.71% |
| 0.70 | 100% | 100% | 100% |

The selected threshold successfully detected a paraphrased document pair with cosine similarity of approximately 0.7152.

These results apply only to the synthetic development dataset. Threshold selection and evaluation used the same dataset, so the results do not establish generalization to unseen submissions.

Additional evaluation details are available in `EVALUATION.md`.

## Production Scaling Architecture: 10,000 Submissions

The prototype uses exact NumPy similarity comparisons. For production-scale workloads, the following architecture is proposed:

```text
Submission Upload
        |
Object Storage
        |
Redis / Celery Task Queue
        |
Parallel CPU and GPU Workers
        |
Vector Database with HNSW Index
        |
Similarity Detection Service
        |
PostgreSQL Metadata Storage
        |
Integrity Reports
```

### Compute Strategy

- CPU workers for PDF and DOCX extraction.
- GPU workers for Whisper transcription and batched embedding inference.
- Asynchronous processing using Redis and Celery.
- Independent worker scaling based on queue size.

### Vector Indexing

An HNSW-based approximate nearest-neighbor index can replace exhaustive NumPy comparisons at larger scales.

HNSW improves retrieval latency at the expense of additional memory consumption and potentially missed nearest neighbors. Exact cosine similarity can be used to rerank retrieved candidates.

### Storage

- Object storage for submission files.
- PostgreSQL for document metadata, task status, and audit references.
- Vector storage for embeddings and chunk identifiers.

### Cost and Performance

Assuming 20 chunks per submission, 10,000 submissions would produce approximately 200,000 embeddings.

At 384 dimensions using float32, the raw embedding vectors would require approximately 307 MB of storage, excluding metadata and index overhead.

An exhaustive similarity matrix would require approximately 160 GB of float32 storage if fully materialized. Approximate nearest-neighbor retrieval and batched comparisons would avoid this requirement.

Video transcription is expected to be a major computational bottleneck. Batch inference, caching, asynchronous workers, and incremental indexing can improve throughput.

These are architectural estimates rather than measured production benchmarks.

## Assumptions

- Input documents primarily contain English text.
- PDF files contain extractable text rather than scanned images.
- Video submissions are short and contain spoken content.
- Local external references simulate web plagiarism detection.
- Similarity indicates potential overlap rather than definitive misconduct.
- Human reviewers make final integrity decisions.

## Limitations

- Small synthetic evaluation dataset.
- Threshold tuning and evaluation use the same samples.
- No independent generalization benchmark.
- External reference coverage is limited.
- AI estimation is an uncalibrated mock heuristic.
- Scanned PDF OCR is not implemented.
- Production scalability has not been load-tested.
- DOCX locations use paragraph references rather than rendered page numbers.

## Future Improvements

- Independent validation and test datasets.
- FAISS or HNSW vector indexing.
- Sentence-level semantic matching and cross-encoder reranking.
- OCR support for scanned documents.
- Multilingual speech and text processing.
- Calibrated AI content classification.
- Distributed processing and production monitoring.

## AI Assistance Disclosure

ChatGPT was used extensively to generate the initial project implementation, synthetic dataset, documentation drafts, and debugging guidance.

Local environment configuration, pipeline execution, threshold experiments, report inspection, and automated testing were subsequently performed by the candidate with AI guidance.

The candidate should independently review and understand the implementation and confirm that the scope of AI assistance complies with the assessment rules before submission.
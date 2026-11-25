"""Normalized embeddings and exact NumPy inner-product index."""
import numpy as np


class Encoder:
    def __init__(self, backend='semantic'):
        self.backend = backend
        if backend == 'semantic':
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        else:
            from sklearn.feature_extraction.text import HashingVectorizer
            self.model = HashingVectorizer(n_features=4096, alternate_sign=False, ngram_range=(1, 2), norm='l2')

    def encode(self, texts):
        if self.backend == 'semantic':
            return np.asarray(self.model.encode(texts, normalize_embeddings=True), dtype=np.float32)
        return self.model.transform(texts).toarray().astype(np.float32)


class VectorIndex:
    def __init__(self, entries, encoder):
        self.entries = entries
        self.vectors = encoder.encode([c['text'] for _, c in entries]) if entries else None

    def search(self, query, exclude=None, threshold=.8):
        if self.vectors is None:
            return []
        scores = self.vectors @ query
        return [(name, c, float(min(1, scores[i]))) for i, (name, c) in enumerate(self.entries)
                if name != exclude and scores[i] >= threshold]

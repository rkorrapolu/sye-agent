"""Embedding generation for semantic similarity."""
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib


class EmbeddingGenerator:
    """Generates embeddings for semantic similarity using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding generator.

        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
                       - 384 dimensions
                       - Fast inference
                       - Good quality for semantic search
        """
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded ({self.embedding_dim} dimensions)")

    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Numpy array of shape (embedding_dim,)
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            Numpy array of shape (len(texts), embedding_dim)
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings

    @staticmethod
    def hash_text(text: str) -> str:
        """
        Generate a hash for text (useful for cache keys).

        Args:
            text: Input text

        Returns:
            SHA256 hash hex string
        """
        return hashlib.sha256(text.encode()).hexdigest()[:16]


# Global instance (lazy-loaded)
_embedding_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator() -> EmbeddingGenerator:
    """
    Get or create global embedding generator instance.

    Returns:
        Singleton EmbeddingGenerator instance
    """
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator

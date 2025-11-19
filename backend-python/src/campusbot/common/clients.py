"""
Shared embedding model client for CampusBot.
Provides centralized embedding function configuration.

PURPOSE:
Both ingestion worker and query service need the same embedding model
to ensure consistent vector representations.

EMBEDDING MODEL:
- Model: all-MiniLM-L6-v2 from sentence-transformers
- Dimensions: 384 (each text chunk → 384-dimensional vector)
- Speed: Fast inference (< 100ms per chunk)
- Quality: Good for semantic similarity
- Size: ~80MB model download

WHY SENTENCE TRANSFORMERS:
- Optimized for semantic similarity (not just word matching)
- "What is AI?" and "Define artificial intelligence" → similar vectors
- Trained on paraphrase detection tasks
- Better than simple word2vec or TF-IDF for question answering

CONSISTENCY IMPORTANCE:
- Same model must be used for ingestion and querying
- Different models = different vector spaces = no meaningful similarity
- If ingestion uses model A and query uses model B → search doesn't work
- This shared client ensures consistency across services
"""

from chromadb.utils import embedding_functions

# Initialize sentence transformer embedding function
# This is used by ChromaDB to automatically generate embeddings
model = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"  # 384-dimensional embeddings, good balance of speed/quality
)

def getModel():
    """
    Returns the shared embedding model for use across services.
    
    USAGE:
    - Ingestion worker: uses this for storing document chunks
    - Query service: uses this for converting questions to vectors
    - ChromaDB: automatically calls this to generate embeddings
    
    Returns:
        SentenceTransformerEmbeddingFunction: Configured embedding model
    """
    return model
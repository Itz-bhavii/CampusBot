from chromadb.utils import embedding_functions

model = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def getModel():
    return model
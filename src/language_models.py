from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbeddings:
    """Wrapper for SentenceTransformers model to work with LangChain vector stores."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)  # Ensure NumPy array
        return embeddings.tolist()  # Convert array to list of lists

    def embed_query(self, text: str) -> List[float]:
        """Generate an embedding for a single query."""
        embedding = self.model.encode(text, convert_to_numpy=True)  # Ensure NumPy array
        return embedding.tolist()  # Convert array to a list

embedding_model = SentenceTransformerEmbeddings("all-MiniLM-L6-v2")

base_llm = ChatOpenAI(openai_api_key=os.getenv('whiskey_key'), model='gpt-4o-mini', temperature=0.5)
from app.core.ingestion import get_embeddings, load_vectorstore
from app.config import CHROMA_DIR, TOP_K
import os

def get_retriever():
    embeddings = get_embeddings()

    if not os.path.exists(CHROMA_DIR) or not os.listdir(CHROMA_DIR):
        raise FileNotFoundError(
            "ChromaDB not found. Run ingestion first: python ingest.py"
        )

    vectorstore = load_vectorstore(embeddings)

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K}
    )
    print(f"✅ Retriever ready — will fetch top {TOP_K} chunks per query")
    return retriever
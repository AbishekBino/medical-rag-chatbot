"""
Run this once to ingest all your PDFs into ChromaDB.
After this, ChromaDB is saved to disk — you never need to run this again
unless you add new PDFs.

Usage: python ingest.py
"""
from app.core.ingestion import run_ingestion
from app.core.retriever import get_retriever

if __name__ == "__main__":
    # Step 1: Build the vector store
    run_ingestion()

    print("\n--- Testing Retrieval ---")

    # Step 2: Test retrieval with a sample question
    retriever = get_retriever()
    query = "What is the recommended treatment for hypertension?"
    results = retriever.invoke(query)

    print(f"\n🔍 Query: '{query}'")
    print(f"📄 Top {len(results)} chunks retrieved:\n")

    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "unknown")
        page   = doc.metadata.get("page", "?")
        print(f"  Chunk {i} — {source} (page {page})")
        print(f"  {doc.page_content[:200]}...")
        print()
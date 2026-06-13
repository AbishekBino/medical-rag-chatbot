from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter  
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from app.config import (
    PDF_DIR, CHROMA_DIR,
    CHUNK_SIZE, CHUNK_OVERLAP,
    EMBEDDING_MODEL
)

def load_documents():
    """Step 1: Read all PDFs from data/pdfs/ folder"""
    print(f"📂 Loading PDFs from '{PDF_DIR}'...")
    loader = PyPDFDirectoryLoader(PDF_DIR)
    documents = loader.load()
    print(f"✅ Loaded {len(documents)} pages across all PDFs")
    return documents


def split_documents(documents):
    """Step 2: Split pages into small chunks"""
    print(f"✂️  Splitting into chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]  # tries to split at paragraphs first
    )
    chunks = splitter.split_documents(documents)
    print(f"✅ Created {len(chunks)} chunks")
    return chunks


def get_embeddings():
    """Step 3: Load the embedding model (runs locally, no API key needed)"""
    print(f"🤖 Loading embedding model '{EMBEDDING_MODEL}'...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}
    )
    print("✅ Embedding model loaded")
    return embeddings


def build_vectorstore(chunks, embeddings):
    """Step 4: Convert chunks to vectors and save to ChromaDB"""
    print(f"💾 Building ChromaDB vector store at '{CHROMA_DIR}'...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    print(f"✅ Vector store built and saved — {len(chunks)} chunks indexed")
    return vectorstore


def load_vectorstore(embeddings):
    """Load an existing ChromaDB (use this after first build)"""
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )
    return vectorstore


def run_ingestion():
    """Run the full pipeline: PDF → Chunks → Embeddings → ChromaDB"""
    docs   = load_documents()
    chunks = split_documents(docs)
    emb    = get_embeddings()
    vs     = build_vectorstore(chunks, emb)
    return vs
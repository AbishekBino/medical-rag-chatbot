import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"

from dotenv import load_dotenv
load_dotenv()  # reads your .env file automatically

# ── API Keys ──────────────────────────────────────
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY")
LANGCHAIN_API_KEY  = os.getenv("LANGCHAIN_API_KEY")
TAVILY_API_KEY     = os.getenv("TAVILY_API_KEY")

# ── Paths ─────────────────────────────────────────
import pathlib
BASE_DIR     = pathlib.Path(__file__).parent.parent  # always points to project root
PDF_DIR      = str(BASE_DIR / "data/pdfs")
CHROMA_DIR   = str(BASE_DIR / "data/chroma_db")

# ── Chunking settings ─────────────────────────────
CHUNK_SIZE    = 800   # characters per chunk
CHUNK_OVERLAP = 150   # overlap between chunks (avoids cutting mid-sentence)

# ── Embedding model ───────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # free, runs locally

# ── LLM settings ──────────────────────────────────
LLM_MODEL = "models/gemini-flash-lite-latest"  # ✅ correct for v1beta      #
TEMPERATURE  = 0.2    # low = more factual, less creative (good for medical)
# ── Retriever settings ────────────────────────────
TOP_K = 4  # how many chunks to retrieve per question
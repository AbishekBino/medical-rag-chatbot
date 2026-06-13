from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

# ── Create FastAPI app ────────────────────────────────────────────────────
app = FastAPI(
    title="Medical RAG Chatbot API",
    description="Ask questions about medical documents using AI",
    version="1.0.0"
)

# ── CORS Middleware ───────────────────────────────────────────────────────
# CORS = Cross Origin Resource Sharing
# Without this, your React frontend (running on port 3000) 
# CANNOT talk to this FastAPI server (running on port 8000).
# The browser blocks it for security. This middleware lifts that block.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:3000",
    "http://localhost:5173",
    "https://medical-rag-chatbot-seven.vercel.app",
],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all routes under /api prefix ─────────────────────────────────
# This means: /chat becomes /api/chat, /health becomes /api/health, etc.
app.include_router(router, prefix="/api")


# ── Root route ────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "Medical RAG Chatbot API",
        "docs": "/docs",         # FastAPI auto-generates this — very useful
        "health": "/api/health"
    }
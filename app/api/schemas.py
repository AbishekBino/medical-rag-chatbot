from pydantic import BaseModel
from typing import List, Optional


# ── Request shapes (what the CLIENT sends TO us) ──────────────────────────

class ChatRequest(BaseModel):
    """What the frontend sends when user asks a question"""
    question: str
    session_id: str = "default"   # which user's memory to use


class UploadResponse(BaseModel):
    """What we send back after a PDF upload"""
    message: str
    filename: str
    chunks_added: int


# ── Response shapes (what WE send BACK to client) ─────────────────────────

class SourceDocument(BaseModel):
    """A single source citation"""
    file: str
    page: int


class ChatResponse(BaseModel):
    """What we send back after answering a question"""
    answer: str
    sources: List[SourceDocument]
    session_id: str


class HealthResponse(BaseModel):
    """Simple health check response"""
    status: str
    message: str
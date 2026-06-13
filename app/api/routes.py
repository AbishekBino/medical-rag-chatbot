from fastapi import APIRouter, HTTPException, UploadFile, File
from app.api.schemas import ChatRequest, ChatResponse, UploadResponse, HealthResponse, SourceDocument
from app.core.rag_chain import build_rag_chain, parse_response
from app.core.agent import build_agent, extract_text_from_output
from app.memory.session import get_session_memory, clear_session_memory
from app.core.ingestion import get_embeddings, build_vectorstore, split_documents
from langchain_community.document_loaders import PyPDFLoader
from app.config import PDF_DIR
import shutil
import os
import re

router = APIRouter()


# ── 1. Health Check ───────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Simple ping to check if the server is alive.
    Frontend calls this on startup to confirm backend is running.
    """
    return HealthResponse(
        status="ok",
        message="RAG Chatbot backend is running"
    )


# ── 2. Chat Endpoint ──────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main endpoint. Takes a question + session_id, returns answer + sources.

    Flow:
    1. Get (or create) memory for this session
    2. Build the RAG chain with that memory
    3. Ask the question
    4. Parse and return the response
    """
    try:
        # Get this user's memory (creates new one if first message)
        memory = get_session_memory(request.session_id)

        # Build chain with that memory
        chain = build_rag_chain(memory)

        # Ask the question
        raw_response = chain.invoke({"question": request.question})

        # Clean up the response
        result = parse_response(raw_response)

        # Build source list
        sources = [
            SourceDocument(file=s["file"], page=s["page"])
            for s in result["sources"]
        ]

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            session_id=request.session_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 3. Upload PDF Endpoint ────────────────────────────────────────────────
@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a new PDF and add it to ChromaDB without restarting the server.

    Flow:
    1. Save PDF to data/pdfs/
    2. Load + chunk just that file
    3. Add chunks to existing ChromaDB
    """
    # Only accept PDFs
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        # Save the uploaded file to disk
        save_path = os.path.join(PDF_DIR, file.filename)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Load and chunk just this new file
        loader = PyPDFLoader(save_path)
        pages = loader.load()
        chunks = split_documents(pages)

        # Add to existing ChromaDB
        embeddings = get_embeddings()
        build_vectorstore(chunks, embeddings)

        return UploadResponse(
            message="PDF uploaded and indexed successfully",
            filename=file.filename,
            chunks_added=len(chunks)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 4. Clear History Endpoint ─────────────────────────────────────────────
@router.delete("/history/{session_id}")
def clear_history(session_id: str):
    """
    Clears conversation memory for a specific session.
    User clicks 'New Chat' on the frontend → this gets called.
    """
    clear_session_memory(session_id)
    return {"message": f"Chat history cleared for session '{session_id}'"}


# ── 5. Agentic Chat Endpoint (RAG + Web Fallback) ─────────────────────────
_agent_instance = None


def get_agent():
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = build_agent()
    return _agent_instance


@router.post("/chat-agent", response_model=ChatResponse)
def chat_agent(request: ChatRequest):
    """
    Like /chat, but uses an agent that can fall back to web search
    if the medical PDFs don't have the answer.
    """
    try:
        agent = get_agent()
        memory = get_session_memory(request.session_id)

        # Convert memory's messages into the format the agent expects
        chat_history = memory.chat_memory.messages

        response = agent.invoke({
            "input": request.question,
            "chat_history": chat_history
        })

        # Extract clean text from Gemini's response (handles list-of-blocks format)
        answer_text = extract_text_from_output(response["output"])

        # Save this exchange into memory for future turns
        memory.chat_memory.add_user_message(request.question)
        memory.chat_memory.add_ai_message(answer_text)

        # Extract sources from intermediate steps (if search_medical_docs was used)
        sources = []
        for action, observation in response["intermediate_steps"]:
            if action.tool == "search_medical_docs" and "page" in observation:
                matches = re.findall(r"\[(.*?), page (\d+|\?)\]", observation)
                for fname, page in matches:
                    sources.append(SourceDocument(file=fname, page=int(page) if page != "?" else 0))

        return ChatResponse(
            answer=answer_text,
            sources=sources[:4],  # limit to top 4
            session_id=request.session_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
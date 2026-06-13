import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from app.core.retriever import get_retriever
from app.config import GEMINI_API_KEY, LLM_MODEL, TEMPERATURE


# ── Custom Prompt ──────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """
You are a helpful medical information assistant.
Answer the user's question using ONLY the context provided below.
If the answer is not in the context, say "I don't have enough information
in my documents to answer this. Please consult a medical professional."

Always cite which document your answer came from at the end.

Context from documents:
{context}

Chat History:
{chat_history}

User Question: {question}

Answer:
"""

prompt = PromptTemplate(
    input_variables=["context", "chat_history", "question"],
    template=PROMPT_TEMPLATE
)


def get_llm():
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=TEMPERATURE,
        convert_system_message_to_human=True
    )
    return llm


def create_memory():
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    return memory


def build_rag_chain(memory: ConversationBufferMemory):
    retriever = get_retriever()
    llm = get_llm()

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
        verbose=True
    )
    print("✅ RAG chain built successfully")
    return chain


def parse_response(response: dict) -> dict:
    answer = response.get("answer", "")
    sources = []
    seen = set()
    for doc in response.get("source_documents", []):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        key = f"{source}:{page}"
        if key not in seen:
            seen.add(key)
            sources.append({
                "file": source.split("/")[-1].split("\\")[-1],
                "page": page
            })
    return {"answer": answer, "sources": sources}
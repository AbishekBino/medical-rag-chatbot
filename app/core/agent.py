from langchain_classic.agents import create_tool_calling_agent, AgentExecutor   # ✅
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools.tavily_search import TavilySearchResults
from app.core.rag_chain import get_llm, get_cached_retriever
from app.config import TAVILY_API_KEY


# ── Tool 1: Search Your Medical PDFs ───────────────────────────────────────
@tool
def search_medical_docs(query: str) -> str:
    """
    Search the medical knowledge base (WHO/AIIMS guideline PDFs) for
    information relevant to the query. Use this FIRST for any medical,
    clinical, drug, or health-guideline question.
    """
    retriever = get_cached_retriever()
    docs = retriever.invoke(query)

    if not docs:
        return "No relevant information found in the medical documents."

    results = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown").split("/")[-1].split("\\")[-1]
        page = doc.metadata.get("page", "?")
        results.append(f"[{source}, page {page}]: {doc.page_content}")

    return "\n\n".join(results)


# ── Tool 2: Web Search (Tavily) ─────────────────────────────────────────────
search_web = TavilySearchResults(
    max_results=3,
    tavily_api_key=TAVILY_API_KEY,
    description=(
        "Search the web for CURRENT or RECENT information not likely to be "
        "in static medical guideline documents — e.g. news, recent outbreaks, "
        "new drug approvals, or anything time-sensitive. Use this ONLY if "
        "search_medical_docs did not return a useful answer."
    )
)


# ── Agent Prompt ──────────────────────────────────────────────────────────
AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful medical information assistant.

Always try `search_medical_docs` FIRST for any medical/clinical question.
Only use `search_web` if:
- search_medical_docs returns "No relevant information found", OR
- the question explicitly asks about current events, news, or recent updates.

When you answer using search_medical_docs results, cite the source file and page.
When you answer using search_web results, mention that the information is from a web search.

If neither tool has the answer, say so honestly and suggest consulting a medical professional.
"""),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])


# ── Build the Agent ──────────────────────────────────────────────────────
def build_agent():
    """
    Builds a tool-calling agent that decides between searching
    your medical PDFs or the live web.
    """
    llm = get_llm()
    tools = [search_medical_docs, search_web]

    agent = create_tool_calling_agent(llm, tools, AGENT_PROMPT)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,  # so we can show which tool was used
        max_iterations=4
    )
    print("✅ Agent built with tools: search_medical_docs, search_web")
    return executor
def extract_text_from_output(output) -> str:
    """
    Gemini 2.x agents sometimes return output as a list of content blocks
    (with 'type': 'text' plus internal reasoning signatures) instead of
    a plain string. This extracts just the human-readable text.
    """
    if isinstance(output, str):
        return output

    if isinstance(output, list):
        texts = []
        for block in output:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
            elif isinstance(block, str):
                texts.append(block)
        return "".join(texts)

    return str(output)
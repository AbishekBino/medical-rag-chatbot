from langchain_classic.memory import ConversationBufferMemory

# One memory object per user session, keyed by UUID
memory_store: dict = {}

def get_session_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in memory_store:
        memory_store[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
    return memory_store[session_id]

def clear_session_memory(session_id: str):
    if session_id in memory_store:
        del memory_store[session_id]
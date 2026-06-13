import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api"

const WELCOME_MESSAGE = { role: "bot", text: "Hi! Ask me anything about the medical documents I've been trained on — or any general medical question.", sources: [] }

function App() {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem("rag-chat-messages")
      return saved ? JSON.parse(saved) : [WELCOME_MESSAGE]
    } catch {
      return [WELCOME_MESSAGE]
    }
  })
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem("rag-chat-session-id") || "session-" + Math.random().toString(36).substring(2, 10)
  })
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    localStorage.setItem("rag-chat-messages", JSON.stringify(messages))
  }, [messages])

  useEffect(() => {
    localStorage.setItem("rag-chat-session-id", sessionId)
  }, [sessionId])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = { role: "user", text: input, sources: [] }
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/chat-agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage.text, session_id: sessionId })
      })

      const data = await res.json()

      const botMessage = { role: "bot", text: data.answer, sources: data.sources }
      setMessages(prev => [...prev, botMessage])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: "bot",
        text: "Could not reach the server. Is the backend running?",
        sources: []
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const startNewChat = async () => {
    if (loading) return
    try {
      await fetch(`${API_URL}/history/${sessionId}`, { method: "DELETE" })
    } catch (err) {
      // non-fatal — proceed to reset UI regardless
    }
    setMessages([WELCOME_MESSAGE])
    setSessionId("session-" + Math.random().toString(36).substring(2, 10))
  }

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center py-6 px-4">

      {/* Header */}
      <div className="w-full max-w-2xl mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">🩺 Medical RAG Assistant</h1>
          <p className="text-slate-400 text-sm">PDFs + web search enabled</p>
        </div>
        <button
          onClick={startNewChat}
          disabled={loading}
          className="bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white text-sm font-medium rounded-xl px-3 py-2 transition-colors"
        >
          + New chat
        </button>
      </div>

      {/* Chat window */}
      <div className="w-full max-w-2xl flex-1 bg-slate-800 rounded-2xl shadow-lg flex flex-col h-[70vh]">

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>

              {msg.role === "bot" && (
                <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center text-sm flex-shrink-0">
                  🩺
                </div>
              )}

              <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-700 text-slate-100"
              }`}>
                {msg.role === "bot" ? (
                  <div className="text-sm leading-relaxed prose prose-invert prose-sm max-w-none
                                   prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5
                                   prose-strong:text-white prose-headings:text-white">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>
                )}

                {/* Source citations */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-slate-600 flex flex-wrap gap-1">
                    {msg.sources.map((src, j) => (
                      <span key={j} className="text-xs bg-slate-600 text-slate-300 px-2 py-1 rounded-full">
                        📄 {src.file} · p.{src.page}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="w-7 h-7 rounded-full bg-blue-700 flex items-center justify-center text-sm flex-shrink-0">
                  🙂
                </div>
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {loading && (
            <div className="flex gap-2 justify-start">
              <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center text-sm flex-shrink-0">
                🩺
              </div>
              <div className="bg-slate-700 text-slate-300 rounded-2xl px-4 py-3 text-sm">
                <span className="inline-flex gap-1">
                  <span className="animate-bounce">●</span>
                  <span className="animate-bounce [animation-delay:0.1s]">●</span>
                  <span className="animate-bounce [animation-delay:0.2s]">●</span>
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="border-t border-slate-700 p-3 flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a medical question..."
            rows={1}
            className="flex-1 bg-slate-700 text-white rounded-xl px-4 py-2 resize-none outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-xl px-4 py-2 text-sm font-medium transition-colors"
          >
            Send
          </button>
        </div>
      </div>

      <p className="text-slate-500 text-xs mt-3">Session: {sessionId}</p>
    </div>
  )
}

export default App
import { useState, useRef, useEffect } from 'react'

const API_URL = "http://localhost:8000/api"

function App() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hi! Ask me anything about the medical documents I've been trained on.", sources: [] }
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => "session-" + Math.random().toString(36).substring(2, 10))
  const messagesEndRef = useRef(null)

  // Auto-scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = { role: "user", text: input, sources: [] }
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/chat`, {
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
        text: "⚠️ Could not reach the server. Is the backend running?",
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

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center py-6 px-4">

      {/* Header */}
      <div className="w-full max-w-2xl mb-4">
        <h1 className="text-2xl font-bold text-white">🩺 Medical RAG Assistant</h1>
        <p className="text-slate-400 text-sm">Ask questions grounded in WHO &amp; AIIMS guidelines</p>
      </div>

      {/* Chat window */}
      <div className="w-full max-w-2xl flex-1 bg-slate-800 rounded-2xl shadow-lg flex flex-col h-[70vh]">

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-700 text-slate-100"
              }`}>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>

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
            </div>
          ))}

          {/* Typing indicator */}
          {loading && (
            <div className="flex justify-start">
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
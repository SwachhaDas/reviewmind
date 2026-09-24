import React, { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE } from '../api'

/**
 * ChatBox with two modes and session persistence.
 * Listens for external "load-session" events dispatched from ChatPage.
 */
function ChatBox({ contextText, paperTitle, paperData, sessionId, onSessionCreated }) {
  const { t, i18n } = useTranslation()

  const [mode, setMode] = useState(contextText ? 'paper' : 'free')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentSession, setCurrentSession] = useState(sessionId || '')

  const messagesEndRef = useRef(null)

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Reset chat when paper changes
  useEffect(() => {
    setMessages([])
    setError('')
    setCurrentSession('')
    setMode(contextText ? 'paper' : 'free')
  }, [contextText, paperTitle])

  // ─────────────────────────────────────────────────────────
  // Load a session's messages from backend
  // ─────────────────────────────────────────────────────────
  const loadSession = async (sessionIdToLoad) => {
    if (!sessionIdToLoad) return
    try {
      const res = await fetch(`${API_BASE}/chat/history/${sessionIdToLoad}`)
      const session = await res.json()
      if (session && session.messages) {
        setMessages(
          session.messages.map((m) => ({
            role: m.role,
            text: m.text,
          }))
        )
        setCurrentSession(sessionIdToLoad)
        // Auto-switch mode
        setMode(session.source === 'paper' && contextText ? 'paper' : 'free')
      }
    } catch (err) {
      console.error('Load session failed:', err)
      setError('Failed to load session')
    }
  }

  // Listen for external "load-session" events
  useEffect(() => {
    const handler = (e) => {
      if (e.detail && e.detail.sessionId) {
        loadSession(e.detail.sessionId)
      }
    }
    window.addEventListener('load-session', handler)
    return () => window.removeEventListener('load-session', handler)
  }, [contextText])

  const sendMessage = async () => {
    const question = input.trim()
    if (!question) return

    if (mode === 'paper' && (!contextText || !contextText.trim())) {
      setError(t('chatNoContext'))
      return
    }

    // Add user message immediately
    const userMsg = { role: 'user', text: question }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context_text: mode === 'paper' ? contextText : '',
          question: question,
          lang: i18n.language,
          mode: mode,
          session_id: currentSession,
          paper_title: paperTitle || '',
          // Pass paper data so it can be saved with the session
          paper_full_text: paperData?.full_text || '',
          paper_abstract: paperData?.abstract || '',
          paper_introduction: paperData?.introduction || '',
          paper_methodology: paperData?.methodology || '',
          paper_findings: paperData?.findings || '',
          paper_limitations: paperData?.limitations || '',
          paper_conclusion: paperData?.conclusion || '',
          paper_key_points: paperData?.key_points || [],
          paper_content_type: paperData?.content_type || '',
        }),
      })

      const data = await res.json()
      if (data.answer) {
        setMessages((prev) => [...prev, { role: 'assistant', text: data.answer }])
        if (data.session_id && data.session_id !== currentSession) {
          setCurrentSession(data.session_id)
          if (onSessionCreated) onSessionCreated(data.session_id)
        }
      } else {
        setError(data.error || t('chatError'))
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([])
    setError('')
    setCurrentSession('')
  }

  return (
    <div className="bg-white border rounded-lg flex flex-col h-[600px]">
      {/* Header */}
      <div className="border-b">
        <div className="flex items-center justify-between px-4 py-2">
          <h3 className="font-semibold text-gray-800">
            💬 {t('chatTitle')}
          </h3>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="text-xs text-gray-500 hover:text-red-600 transition"
            >
              🗑️ {t('chatClear')}
            </button>
          )}
        </div>

        {/* Mode toggle */}
        <div className="flex gap-1 px-4 pb-2">
          <button
            onClick={() => setMode('paper')}
            disabled={!contextText}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
              mode === 'paper'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            } ${!contextText ? 'opacity-40 cursor-not-allowed' : ''}`}
          >
            📄 {t('modePaper')}
          </button>
          <button
            onClick={() => setMode('free')}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
              mode === 'free'
                ? 'bg-purple-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            🌐 {t('modeFree')}
          </button>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
        {messages.length === 0 && !loading && (
          <div className="text-center text-gray-400 mt-16">
            <p className="text-4xl mb-2">
              {mode === 'paper' ? '📄' : '🌐'}
            </p>
            <p className="text-sm">
              {mode === 'paper' ? t('chatEmptyState') : t('askAnyQuestion')}
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white border text-gray-800'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 bg-red-100 text-red-700 text-sm border-t">
          ❌ {error}
        </div>
      )}

      {/* Input area */}
      <div className="border-t p-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={mode === 'paper' ? t('chatAskPlaceholder') : t('askAnyQuestion')}
            disabled={loading}
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-400 disabled:bg-gray-100 text-sm"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 text-sm"
          >
            {t('chatSendButton')} →
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatBox
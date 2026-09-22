import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE } from '../api'

/**
 * Chat History Sidebar — modern, professional design.
 * Used inside a sliding overlay panel from ChatPage.
 */
function ChatHistory({ refreshKey, onSelectSession }) {
  const { t } = useTranslation()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeId, setActiveId] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/chat/history`)
      const data = await res.json()
      setSessions(data.sessions || [])
    } catch (err) {
      console.error('History fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [refreshKey])

  const handleDelete = async (sessionId, e) => {
    e.stopPropagation()
    if (!window.confirm('Delete this chat session?')) return

    try {
      await fetch(`${API_BASE}/chat/history/${sessionId}`, {
        method: 'DELETE',
      })
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (activeId === sessionId) setActiveId(null)
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const handleClearAll = async () => {
    if (sessions.length === 0) return
    if (!window.confirm(`Delete all ${sessions.length} sessions?`)) return

    try {
      await fetch(`${API_BASE}/chat/history`, { method: 'DELETE' })
      setSessions([])
      setActiveId(null)
    } catch (err) {
      console.error('Clear all failed:', err)
    }
  }

  const handleSelect = (sessionId) => {
    setActiveId(sessionId)
    if (onSelectSession) onSelectSession(sessionId)
  }

  // Group sessions by date
  const groupSessions = (list) => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    const groups = { today: [], yesterday: [], older: [] }

    list.forEach((s) => {
      const d = new Date(s.updated_at || s.created_at)
      d.setHours(0, 0, 0, 0)
      if (d >= today) groups.today.push(s)
      else if (d >= yesterday) groups.yesterday.push(s)
      else groups.older.push(s)
    })

    return groups
  }

  // Filter by search query
  const filtered = searchQuery.trim()
    ? sessions.filter(
        (s) =>
          s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (s.paper_title &&
            s.paper_title.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : sessions

  const grouped = groupSessions(filtered)

  // Relative time formatting
  const formatTime = (isoString) => {
    if (!isoString) return ''
    try {
      const d = new Date(isoString)
      const now = new Date()
      const diffMs = now - d
      const diffMin = Math.floor(diffMs / 60000)
      const diffHr = Math.floor(diffMs / 3600000)
      const diffDay = Math.floor(diffMs / 86400000)

      if (diffMin < 1) return 'just now'
      if (diffMin < 60) return `${diffMin}m ago`
      if (diffHr < 24) return `${diffHr}h ago`
      if (diffDay < 7) return `${diffDay}d ago`
      return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
    } catch {
      return ''
    }
  }

  const SessionCard = ({ session }) => {
    const isActive = activeId === session.id
    const isPaper = session.source === 'paper'

    return (
      <div
        onClick={() => handleSelect(session.id)}
        className={`group relative cursor-pointer rounded-xl border transition-all duration-150 ${
          isActive
            ? 'border-blue-500 bg-gradient-to-r from-blue-50 to-blue-100 shadow-sm'
            : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50 hover:shadow-sm'
        }`}
      >
        <div className="p-3">
          {/* Header row */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <span
                className={`flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs ${
                  isPaper
                    ? 'bg-blue-100 text-blue-600'
                    : 'bg-purple-100 text-purple-600'
                }`}
              >
                {isPaper ? '📄' : '🌐'}
              </span>
              <p
                className={`text-xs font-semibold truncate ${
                  isActive ? 'text-blue-800' : 'text-gray-800'
                }`}
              >
                {session.title}
              </p>
            </div>

            <button
              onClick={(e) => handleDelete(session.id, e)}
              className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition text-xs flex-shrink-0"
              title="Delete session"
            >
              ✕
            </button>
          </div>

          {/* Paper title (if exists) */}
          {session.paper_title && isPaper && (
            <p className="text-[10px] text-gray-500 truncate ml-8 mb-1">
              {session.paper_title}
            </p>
          )}

          {/* Meta row */}
          <div className="flex items-center gap-2 ml-8 mt-1">
            <span className="inline-flex items-center gap-1 text-[10px] text-gray-400">
              <span>💬</span>
              {session.message_count}
            </span>
            <span className="text-gray-300">·</span>
            <span className="text-[10px] text-gray-400">
              {formatTime(session.updated_at)}
            </span>
          </div>
        </div>

        {/* Active indicator bar */}
        {isActive && (
          <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-blue-500 rounded-r" />
        )}
      </div>
    )
  }

  return (
    <div className="bg-white flex flex-col overflow-hidden">
      {/* Header with search */}
      <div className="pb-3 border-b border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-gray-800 text-sm">
              📚 {t('chatHistory')}
            </h3>
            {sessions.length > 0 && (
              <span className="text-[10px] font-medium bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                {sessions.length}
              </span>
            )}
          </div>
          {sessions.length > 0 && (
            <button
              onClick={handleClearAll}
              className="text-[10px] text-gray-400 hover:text-red-500 transition flex items-center gap-1"
              title="Clear all"
            >
              🗑️ Clear
            </button>
          )}
        </div>

        {sessions.length > 0 && (
          <div className="relative">
            <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">
              🔍
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search chats..."
              className="w-full pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400 focus:bg-white bg-gray-50 transition"
            />
          </div>
        )}
      </div>

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto py-3 space-y-4">
        {loading && sessions.length === 0 && (
          <div className="flex items-center justify-center py-8">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
              <span
                className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                style={{ animationDelay: '0.15s' }}
              ></span>
              <span
                className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                style={{ animationDelay: '0.3s' }}
              ></span>
            </div>
          </div>
        )}

        {!loading && sessions.length === 0 && (
          <div className="text-center text-gray-400 py-12">
            <div className="text-5xl mb-3">💭</div>
            <p className="text-xs font-medium text-gray-500 mb-1">
              {t('chatNoHistory')}
            </p>
            <p className="text-[10px] text-gray-400">
              Start a chat to see it here
            </p>
          </div>
        )}

        {!loading && filtered.length === 0 && sessions.length > 0 && (
          <div className="text-center text-gray-400 py-8">
            <div className="text-3xl mb-2">🔍</div>
            <p className="text-xs">No matching chats</p>
          </div>
        )}

        {/* Grouped sessions */}
        {grouped.today.length > 0 && (
          <div>
            <h4 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide px-1 mb-2">
              Today
            </h4>
            <div className="space-y-2">
              {grouped.today.map((s) => (
                <SessionCard key={s.id} session={s} />
              ))}
            </div>
          </div>
        )}

        {grouped.yesterday.length > 0 && (
          <div>
            <h4 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide px-1 mb-2">
              Yesterday
            </h4>
            <div className="space-y-2">
              {grouped.yesterday.map((s) => (
                <SessionCard key={s.id} session={s} />
              ))}
            </div>
          </div>
        )}

        {grouped.older.length > 0 && (
          <div>
            <h4 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide px-1 mb-2">
              Older
            </h4>
            <div className="space-y-2">
              {grouped.older.map((s) => (
                <SessionCard key={s.id} session={s} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatHistory
import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE } from '../api'

/**
 * QuizHistory — sidebar with all past quiz sessions.
 * User can click to reload, rename, or delete.
 */
function QuizHistory({ refreshKey, onSelectSession }) {
  const { t } = useTranslation()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeId, setActiveId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [editingTitle, setEditingTitle] = useState('')

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/quiz/history`)
      const data = await res.json()
      setSessions(data.sessions || [])
    } catch (err) {
      console.error('Quiz history fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [refreshKey])

  const handleDelete = async (sessionId, e) => {
    e.stopPropagation()
    if (!window.confirm('Delete this quiz session?')) return
    try {
      await fetch(`${API_BASE}/quiz/history/${sessionId}`, { method: 'DELETE' })
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (activeId === sessionId) setActiveId(null)
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const handleClearAll = async () => {
    if (sessions.length === 0) return
    if (!window.confirm(`Delete all ${sessions.length} quiz sessions?`)) return
    try {
      await fetch(`${API_BASE}/quiz/history`, { method: 'DELETE' })
      setSessions([])
      setActiveId(null)
    } catch (err) {
      console.error('Clear all failed:', err)
    }
  }

  const handleSelect = (sessionId) => {
    if (editingId) return
    setActiveId(sessionId)
    if (onSelectSession) onSelectSession(sessionId)
  }

  const startEdit = (session, e) => {
    e.stopPropagation()
    setEditingId(session.id)
    setEditingTitle(session.title)
  }

  const cancelEdit = (e) => {
    if (e) e.stopPropagation()
    setEditingId(null)
    setEditingTitle('')
  }

  const saveTitle = async (sessionId, e) => {
    if (e) e.stopPropagation()
    const newTitle = editingTitle.trim()
    if (!newTitle) return cancelEdit()
    try {
      await fetch(`${API_BASE}/quiz/history/${sessionId}/title`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      })
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: newTitle } : s))
      )
    } catch (err) {
      console.error('Update title failed:', err)
    } finally {
      cancelEdit()
    }
  }

  const handleEditKey = (e, sessionId) => {
    if (e.key === 'Enter') saveTitle(sessionId)
    if (e.key === 'Escape') cancelEdit()
  }

  const formatTime = (iso) => {
    if (!iso) return ''
    try {
      const d = new Date(iso)
      const diffMin = Math.floor((new Date() - d) / 60000)
      const diffHr = Math.floor(diffMin / 60)
      const diffDay = Math.floor(diffHr / 24)
      if (diffMin < 1) return 'just now'
      if (diffMin < 60) return `${diffMin}m ago`
      if (diffHr < 24) return `${diffHr}h ago`
      if (diffDay < 7) return `${diffDay}d ago`
      return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
    } catch {
      return ''
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm flex flex-col overflow-hidden h-[600px]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-gray-800 text-sm">🎯 Quiz History</h3>
            {sessions.length > 0 && (
              <span className="text-[10px] font-medium bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                {sessions.length}
              </span>
            )}
          </div>
          {sessions.length > 0 && (
            <button
              onClick={handleClearAll}
              className="text-[10px] text-gray-400 hover:text-red-500 transition"
            >
              🗑️ Clear
            </button>
          )}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading && sessions.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-8">Loading…</p>
        )}

        {!loading && sessions.length === 0 && (
          <div className="text-center text-gray-400 py-12">
            <div className="text-5xl mb-3">📝</div>
            <p className="text-xs font-medium text-gray-500 mb-1">No quiz history yet</p>
            <p className="text-[10px] text-gray-400">Generate your first quiz to see it here</p>
          </div>
        )}

        {sessions.map((s) => {
          const isActive = activeId === s.id
          const isEditing = editingId === s.id
          const isCompleted = s.completed && s.score

          return (
            <div
              key={s.id}
              onClick={() => handleSelect(s.id)}
              className={`group cursor-pointer rounded-xl border transition p-3 ${
                isActive
                  ? 'border-blue-500 bg-blue-50 shadow-sm'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
              }`}
            >
              {/* Title row */}
              <div className="flex items-start justify-between gap-2 mb-1">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs bg-purple-100 text-purple-600">
                    {s.source === 'uploaded' ? '📎' : '📝'}
                  </span>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyDown={(e) => handleEditKey(e, s.id)}
                      onBlur={(e) => saveTitle(s.id, e)}
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                      className="flex-1 text-xs font-semibold border border-blue-400 rounded px-1.5 py-0.5 focus:outline-none bg-white"
                    />
                  ) : (
                    <p
                      className={`text-xs font-semibold truncate ${
                        isActive ? 'text-blue-800' : 'text-gray-800'
                      }`}
                    >
                      {s.title}
                    </p>
                  )}
                </div>

                {!isEditing && (
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition">
                    <button
                      onClick={(e) => startEdit(s, e)}
                      className="text-gray-400 hover:text-blue-500 text-xs"
                      title="Rename"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={(e) => handleDelete(s.id, e)}
                      className="text-gray-400 hover:text-red-500 text-xs"
                      title="Delete"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>

              {/* Preview */}
              {s.content_preview && (
                <p className="text-[10px] text-gray-500 truncate ml-8 mb-1">
                  {s.content_preview}
                </p>
              )}

              {/* Meta row */}
              <div className="flex items-center gap-2 ml-8 mt-1 flex-wrap">
                <span className="text-[10px] text-gray-400">
                  ❓ {s.num_questions} Q
                </span>
                <span className="text-gray-300">·</span>
                <span className="text-[10px] text-gray-400">
                  {formatTime(s.updated_at)}
                </span>
                {isCompleted && (
                  <>
                    <span className="text-gray-300">·</span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                        s.score.percentage >= 75
                          ? 'bg-green-100 text-green-700'
                          : s.score.percentage >= 50
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {s.score.percentage}%
                    </span>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default QuizHistory
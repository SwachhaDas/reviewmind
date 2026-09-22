import React, { useState, useEffect } from 'react'
import { REVIEW_ENDPOINTS } from '../api'

/**
 * ReviewHistory — Sliding sidebar listing saved review sessions.
 * Pattern matches ChatHistory / QuizHistory / Presentation history.
 *
 * Props:
 *   refreshKey       (number)   — increment to force a refresh
 *   onSelectSession  (function) — receives session id when clicked
 *   activeSessionId  (string)   — highlight the active session (optional)
 */
function ReviewHistory({ refreshKey, onSelectSession, activeSessionId }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editingTitle, setEditingTitle] = useState('')

  // ─── Fetch history whenever refreshKey changes ───
  useEffect(() => {
    fetchHistory()
  }, [refreshKey])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await fetch(REVIEW_ENDPOINTS.list)
      const data = await res.json()
      if (data.status === 'success') {
        setItems(data.items || [])
      }
    } catch (err) {
      console.error('[ReviewHistory] Fetch failed:', err)
    } finally {
      setLoading(false)
    }
  }

  // ─── Delete a session ───
  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!window.confirm('Delete this review session? This cannot be undone.')) {
      return
    }
    try {
      await fetch(REVIEW_ENDPOINTS.delete(id), { method: 'DELETE' })
      setItems((prev) => prev.filter((item) => item.id !== id))
    } catch (err) {
      console.error('[ReviewHistory] Delete failed:', err)
    }
  }

  // ─── Start editing title ───
  const startEdit = (item, e) => {
    e.stopPropagation()
    setEditingId(item.id)
    setEditingTitle(item.title)
  }

  // ─── Save edited title ───
  const saveEdit = async (id) => {
    const trimmed = (editingTitle || '').trim()
    if (!trimmed) {
      setEditingId(null)
      return
    }
    try {
      await fetch(REVIEW_ENDPOINTS.title(id), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: trimmed }),
      })
      // Update local list
      setItems((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, title: trimmed } : item
        )
      )
      setEditingId(null)
    } catch (err) {
      console.error('[ReviewHistory] Title update failed:', err)
    }
  }

  // ─── Format date nicely ───
  const formatDate = (str) => {
    if (!str) return ''
    // str is "YYYY-MM-DD HH:MM:SS"
    return str.slice(0, 16) // keep "YYYY-MM-DD HH:MM"
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-gray-800">
          📚 Review History
          <span className="ml-2 text-xs font-normal text-gray-500">
            ({items.length})
          </span>
        </h3>
        <button
          onClick={fetchHistory}
          className="text-xs text-gray-500 hover:text-blue-600 transition"
          title="Refresh"
        >
          🔄
        </button>
      </div>

      {/* Loading state */}
      {loading && items.length === 0 && (
        <div className="text-center text-xs text-gray-400 py-6">
          Loading…
        </div>
      )}

      {/* Empty state */}
      {!loading && items.length === 0 && (
        <div className="text-center text-xs text-gray-400 py-8">
          No saved reviews yet.
          <br />
          Run a pipeline to save one automatically.
        </div>
      )}

      {/* List */}
      <div className="space-y-2">
        {items.map((item) => {
          const isActive = item.id === activeSessionId
          const isEditing = editingId === item.id

          return (
            <div
              key={item.id}
              onClick={() => !isEditing && onSelectSession?.(item.id)}
              className={`group p-3 rounded-xl border-2 cursor-pointer transition ${
                isActive
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/40'
              }`}
            >
              <div className="flex items-start gap-2">
                <span className="text-lg">📄</span>
                <div className="flex-1 min-w-0">
                  {/* Title — inline edit */}
                  {isEditing ? (
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      onBlur={() => saveEdit(item.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveEdit(item.id)
                        if (e.key === 'Escape') setEditingId(null)
                      }}
                      autoFocus
                      className="w-full text-sm font-medium border border-blue-400 rounded px-2 py-0.5 focus:outline-none"
                    />
                  ) : (
                    <h4 className="text-sm font-semibold text-gray-800 truncate">
                      {item.title}
                    </h4>
                  )}

                  {/* Meta row */}
                  <div className="flex items-center gap-2 text-[11px] text-gray-500 mt-1 flex-wrap">
                    <span>{item.paper_count} papers</span>
                    <span>·</span>
                    <span className="text-green-600 font-medium">
                      ✓ {item.included_count}
                    </span>
                    <span className="text-red-600 font-medium">
                      ✕ {item.excluded_count}
                    </span>
                  </div>

                  <div className="text-[10px] text-gray-400 mt-1">
                    {formatDate(item.created_at)}
                  </div>

                  {/* Badges */}
                  <div className="flex items-center gap-1 mt-1.5">
                    {item.has_report && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 font-medium">
                        📄 Report
                      </span>
                    )}
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium uppercase">
                      {item.language || 'en'}
                    </span>
                  </div>
                </div>

                {/* Hover actions */}
                <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition">
                  <button
                    onClick={(e) => startEdit(item, e)}
                    className="text-xs text-gray-500 hover:text-blue-600 px-1"
                    title="Edit title"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="text-xs text-gray-500 hover:text-red-600 px-1"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ReviewHistory
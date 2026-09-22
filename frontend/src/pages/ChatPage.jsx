import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE } from '../api'
import PaperUpload from '../components/PaperUpload'
import PaperSections from '../components/PaperSections'
import ChatBox from '../components/ChatBox'
import ChatHistory from '../components/ChatHistory'

function ChatPage() {
  const { t } = useTranslation()
  const [paper, setPaper] = useState(null)
  const [historyKey, setHistoryKey] = useState(0)
  const [showHistory, setShowHistory] = useState(false)

  const handlePaperLoaded = (loadedPaper) => {
    setPaper(loadedPaper)
  }

  const handleResetPaper = () => {
    setPaper(null)
  }

  const handleSessionCreated = () => {
    // Refresh history sidebar
    setHistoryKey((k) => k + 1)
  }

  /**
   * Session click handler:
   * 1) Fetches full session data from backend
   * 2) Loads paper_data into the left side (if available)
   * 3) Dispatches event for ChatBox to load messages
   */
  const handleSelectSession = async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE}/chat/history/${sessionId}`)
      const session = await res.json()

      // Load paper data if present
      if (session.paper_data && Object.keys(session.paper_data).length > 0) {
        const pd = session.paper_data
        setPaper({
          title: pd.title || session.paper_title || 'Untitled',
          full_text: pd.full_text || '',
          abstract: pd.abstract || '',
          introduction: pd.introduction || '',
          methodology: pd.methodology || '',
          findings: pd.findings || '',
          limitations: pd.limitations || '',
          conclusion: pd.conclusion || '',
          key_points: pd.key_points || [],
          content_type: pd.content_type || 'unknown',
          char_count: (pd.full_text || '').length,
          word_count: (pd.full_text || '').split(/\s+/).filter(Boolean).length,
          source: session.source === 'paper' ? 'pasted' : 'free',
        })
      } else if (session.source !== 'paper') {
        // Free chat — no paper content
        setPaper(null)
      }
    } catch (err) {
      console.error('Failed to load session paper data:', err)
    }

    // Notify ChatBox to load messages
    window.dispatchEvent(
      new CustomEvent('load-session', { detail: { sessionId } })
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto relative">
      {/* Header with history toggle */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            💬 {t('navChat')}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {t('chatPageSubtitle')}
          </p>
        </div>

        <button
          onClick={() => setShowHistory(!showHistory)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition shadow-sm ${
            showHistory
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:text-blue-600'
          }`}
        >
          📚 {t('chatHistory')}
          <span className="text-xs opacity-70">
            {showHistory ? '✕' : '→'}
          </span>
        </button>
      </div>

      {/* Sliding history sidebar */}
      <div
        className={`fixed top-0 right-0 h-screen w-full sm:w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
          showHistory ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <h3 className="font-bold text-gray-800 text-sm">
            📚 {t('chatHistory')}
          </h3>
          <button
            onClick={() => setShowHistory(false)}
            className="text-gray-500 hover:text-red-500 text-lg px-2 transition font-bold"
          >
            ✕
          </button>
        </div>

        <div
          className="p-4 overflow-y-auto"
          style={{ height: 'calc(100vh - 60px)' }}
        >
          <ChatHistory
            refreshKey={historyKey}
            onSelectSession={handleSelectSession}
          />
        </div>
      </div>

      {/* Backdrop for sidebar */}
      {showHistory && (
        <div
          onClick={() => setShowHistory(false)}
          className="fixed inset-0 bg-black bg-opacity-30 z-40"
        />
      )}

      {/* Main content */}
      {!paper ? (
        <div className="max-w-3xl mx-auto">
          <PaperUpload onPaperLoaded={handlePaperLoaded} />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: Paper sections */}
          <div className="lg:col-span-2">
            <div className="flex justify-end mb-2">
              <button
                onClick={handleResetPaper}
                className="text-xs text-gray-500 hover:text-red-600 transition"
              >
                🔄 {t('chatChangePaper')}
              </button>
            </div>
            <PaperSections paper={paper} />
          </div>

          {/* Right: ChatBox */}
          <div className="lg:col-span-3">
            <ChatBox
              contextText={paper.full_text || paper.abstract}
              paperTitle={paper.title}
              paperData={paper}
              onSessionCreated={handleSessionCreated}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default ChatPage
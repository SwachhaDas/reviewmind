import React, { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE, PRESENTATION_ENDPOINTS } from '../api'
import SlidePreview from '../components/SlidePreview'

function PresentationPage() {
  const { t, i18n } = useTranslation()

  // ─── Input state ───
  const [mode, setMode] = useState('paste')
  const [contentText, setContentText] = useState('')
  const [titleHint, setTitleHint] = useState('')
  const [fileName, setFileName] = useState('')

  // ─── Loading & error ───
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // ─── Result state ───
  const [slides, setSlides] = useState([])
  const [presTitle, setPresTitle] = useState('')
  const [presSubtitle, setPresSubtitle] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [pptxUrl, setPptxUrl] = useState('')
  const [pdfUrl, setPdfUrl] = useState('')

  // ─── History ───
  const [showHistory, setShowHistory] = useState(false)
  const [historyItems, setHistoryItems] = useState([])
  const [editingId, setEditingId] = useState(null)
  const [editingTitle, setEditingTitle] = useState('')

  const fileInputRef = useRef(null)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const res = await fetch(PRESENTATION_ENDPOINTS.history)
      const data = await res.json()
      if (data.status === 'success') {
        setHistoryItems(data.items || [])
      }
    } catch (err) {
      console.error('History fetch failed:', err)
    }
  }

  // ─── File upload handler ───
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    const name = file.name.toLowerCase()
    const isPdf = name.endsWith('.pdf')
    const isText = name.endsWith('.txt') || name.endsWith('.md')

    if (!isPdf && !isText) {
      setError('Only PDF, TXT, or MD files are supported')
      return
    }

    setLoading(true)
    setError('')

    try {
      if (isText) {
        const text = await file.text()
        setContentText(text)
        setFileName(file.name)
        setMode('paste')
      } else {
        const formData = new FormData()
        formData.append('file', file)

        const res = await fetch(`${API_BASE}/upload`, {
          method: 'POST',
          body: formData,
        })
        const data = await res.json()
        if (data.status !== 'success') {
          throw new Error(data.message || 'Upload failed')
        }
        const text = data.full_text || data.abstract || ''
        setContentText(text)
        setFileName(file.name)
        setMode('paste')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // ─── Generate presentation ───
  const handleGenerate = async () => {
    if (!contentText.trim()) {
      setError('Please provide content to generate the presentation.')
      return
    }

    setLoading(true)
    setError('')
    setSlides([])
    setPresTitle('')
    setPresSubtitle('')
    setSessionId(null)
    setPptxUrl('')
    setPdfUrl('')

    try {
      const res = await fetch(PRESENTATION_ENDPOINTS.generate, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: contentText,
          title: titleHint || null,
          lang: i18n.language || 'en',
        }),
      })

      const data = await res.json()

      if (data.status === 'success') {
        setSlides(data.slides || [])
        setPresTitle(data.title || 'Presentation')
        setPresSubtitle(data.subtitle || '')
        setSessionId(data.session_id)
        setPptxUrl(`${API_BASE.replace('/api', '')}${data.pptx_url}`)
        setPdfUrl(`${API_BASE.replace('/api', '')}${data.pdf_url}`)
        fetchHistory()
      } else {
        setError(data.detail || 'Generation failed')
      }
    } catch (err) {
      console.error('Presentation error:', err)
      setError(err.message || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  // ─── Download helper ───
  const handleDownload = (url) => {
    if (!url) return
    const a = document.createElement('a')
    a.href = url
    a.target = '_blank'
    a.rel = 'noopener noreferrer'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  // ─── Load session from history ───
  const handleSelectSession = async (id) => {
    try {
      const res = await fetch(PRESENTATION_ENDPOINTS.session(id))
      const data = await res.json()
      if (data.status !== 'success') {
        setError(data.detail || 'Failed to load session')
        return
      }

      setSlides(data.slides || [])
      setPresTitle(data.title || 'Presentation')
      setPresSubtitle(data.subtitle || '')
      setSessionId(data.session_id)
      setContentText(data.raw_content || '')
      setPptxUrl(
        data.pptx_url ? `${API_BASE.replace('/api', '')}${data.pptx_url}` : ''
      )
      setPdfUrl(
        data.pdf_url ? `${API_BASE.replace('/api', '')}${data.pdf_url}` : ''
      )
      setError('')

      if (window.innerWidth < 1024) setShowHistory(false)
    } catch (err) {
      console.error('Load session failed:', err)
      setError('Failed to load session')
    }
  }

  // ─── Delete session ───
  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!window.confirm('Delete this presentation? This cannot be undone.')) {
      return
    }
    try {
      await fetch(PRESENTATION_ENDPOINTS.delete(id), { method: 'DELETE' })
      if (id === sessionId) {
        setSlides([])
        setPresTitle('')
        setPresSubtitle('')
        setSessionId(null)
        setPptxUrl('')
        setPdfUrl('')
      }
      fetchHistory()
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  // ─── Title edit ───
  const startEdit = (item, e) => {
    e.stopPropagation()
    setEditingId(item.id)
    setEditingTitle(item.title)
  }

  const saveEdit = async (id) => {
    if (!editingTitle.trim()) {
      setEditingId(null)
      return
    }
    try {
      await fetch(PRESENTATION_ENDPOINTS.title(id), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editingTitle }),
      })
      setEditingId(null)
      fetchHistory()
      if (id === sessionId) {
        setPresTitle(editingTitle)
      }
    } catch (err) {
      console.error('Title update failed:', err)
    }
  }

  // ─── Reset view ───
  const handleReset = () => {
    setSlides([])
    setPresTitle('')
    setPresSubtitle('')
    setSessionId(null)
    setPptxUrl('')
    setPdfUrl('')
    setContentText('')
    setTitleHint('')
    setFileName('')
    setError('')
    setMode('paste')
  }

  // ═══════════════════════════════════════════════
  // HISTORY SIDEBAR
  // ═══════════════════════════════════════════════
  const HistorySidebar = () => (
    <>
      <div
        className={`fixed top-0 right-0 h-screen w-full sm:w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
          showHistory ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <h3 className="font-bold text-gray-800 text-base sm:text-sm">
            📚 {t('presHistory')}
          </h3>
          <button
            onClick={() => setShowHistory(false)}
            className="text-gray-500 hover:text-red-500 text-2xl sm:text-lg w-10 h-10 flex items-center justify-center rounded-lg hover:bg-red-50 transition font-bold"
          >
            ✕
          </button>
        </div>
        <div
          className="p-4 overflow-y-auto"
          style={{ height: 'calc(100vh - 60px)' }}
        >
          {historyItems.length === 0 ? (
            <div className="text-center text-sm text-gray-400 mt-12">
              {t('presNoHistory')}
            </div>
          ) : (
            <div className="space-y-2">
              {historyItems.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSelectSession(item.id)}
                  className={`group p-3 rounded-xl border-2 cursor-pointer transition ${
                    sessionId === item.id
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/40'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg">📊</span>
                    <div className="flex-1 min-w-0">
                      {editingId === item.id ? (
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
                          className="w-full text-base sm:text-sm font-medium border border-blue-400 rounded px-2 py-0.5 focus:outline-none"
                        />
                      ) : (
                        <h4 className="text-sm font-semibold text-gray-800 truncate">
                          {item.title}
                        </h4>
                      )}
                      <div className="flex items-center gap-2 text-[11px] text-gray-500 mt-1 flex-wrap">
                        <span>
                          {item.slide_count} {t('presSlides')}
                        </span>
                        <span>·</span>
                        <span>{item.created_at}</span>
                      </div>
                      <div className="flex items-center gap-1 mt-1">
                        {item.has_pptx && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium">
                            PPTX
                          </span>
                        )}
                        {item.has_pdf && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-medium">
                            PDF
                          </span>
                        )}
                      </div>
                    </div>
                    {/* Action buttons — always visible on mobile (no hover),
                        hover-reveal on desktop. */}
                    <div className="flex flex-col gap-1 transition sm:opacity-0 sm:group-hover:opacity-100">
                      <button
                        onClick={(e) => startEdit(item, e)}
                        className="text-sm sm:text-xs text-gray-500 hover:text-blue-600 p-1.5 sm:p-0 sm:px-1"
                        title={t('presEditTitle')}
                      >
                        ✏️
                      </button>
                      <button
                        onClick={(e) => handleDelete(item.id, e)}
                        className="text-sm sm:text-xs text-gray-500 hover:text-red-600 p-1.5 sm:p-0 sm:px-1"
                        title={t('presDelete')}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showHistory && (
        <div
          onClick={() => setShowHistory(false)}
          className="fixed inset-0 bg-black bg-opacity-30 z-40"
        />
      )}
    </>
  )

  // ═══════════════════════════════════════════════
  // RESULT VIEW (after generation)
  // ═══════════════════════════════════════════════
  if (slides.length > 0) {
    return (
      <div className="px-4 py-4 sm:px-6 sm:py-6 max-w-4xl mx-auto relative">
        {/* Header */}
        <div className="mb-4 sm:mb-5 flex items-center justify-between flex-wrap gap-2 sm:gap-3">
          <div className="flex-1 min-w-0">
            {/* line-clamp-2 lets long titles wrap on mobile instead of
                being cut off by truncate. */}
            <h1 className="text-lg sm:text-xl font-bold text-gray-800 line-clamp-2 break-words">
              🎨 {presTitle}
            </h1>
            {presSubtitle && (
              <p className="text-xs text-gray-500 mt-0.5 truncate">
                {presSubtitle}
              </p>
            )}
          </div>
          {/* Buttons stretch to full width on xs, auto on sm+. */}
          <div className="flex gap-2 flex-shrink-0 w-full sm:w-auto">
            <button
              onClick={handleReset}
              className="flex-1 sm:flex-none px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition"
            >
              ← {t('presNew')}
            </button>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex-1 sm:flex-none px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 bg-white text-gray-700 hover:border-blue-400 transition"
            >
              📚 {t('presHistoryShort')}
            </button>
          </div>
        </div>

        <HistorySidebar />

        {/* Download buttons — stack on mobile */}
        <div className="flex flex-col sm:flex-row flex-wrap gap-2 sm:gap-3 mb-4 sm:mb-5 justify-center">
          <button
            onClick={() => handleDownload(pptxUrl)}
            disabled={!pptxUrl}
            className="px-4 sm:px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold shadow-sm hover:shadow-md transition text-xs sm:text-sm disabled:opacity-50"
          >
            ⬇️ {t('presDownloadPptx')}
          </button>
          <button
            onClick={() => handleDownload(pdfUrl)}
            disabled={!pdfUrl}
            className="px-4 sm:px-5 py-2.5 bg-white border-2 border-blue-500 text-blue-600 hover:bg-blue-50 rounded-lg font-semibold shadow-sm transition text-xs sm:text-sm disabled:opacity-50"
          >
            ⬇️ {t('presDownloadPdf')}
          </button>
        </div>

        <SlidePreview
          slides={slides}
          title={presTitle}
          subtitle={presSubtitle}
        />
      </div>
    )
  }

  // ═══════════════════════════════════════════════
  // INPUT VIEW (default)
  // ═══════════════════════════════════════════════
  return (
    <div className="px-4 py-4 sm:px-6 sm:py-6 max-w-7xl mx-auto relative">
      {/* Header */}
      <div className="mb-4 sm:mb-6 flex items-center justify-between flex-wrap gap-2 sm:gap-3">
        <div className="flex-1 min-w-0">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-800">
            🎨 {t('presentationTitle')}
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            {t('presentationPageSubtitle')}
          </p>
        </div>

        <button
          onClick={() => setShowHistory(!showHistory)}
          className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg border text-xs sm:text-sm font-medium transition shadow-sm ${
            showHistory
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:text-blue-600'
          }`}
        >
          📚 {t('presHistoryShort')}
          <span className="text-xs opacity-70">
            {showHistory ? '✕' : '→'}
          </span>
        </button>
      </div>

      <HistorySidebar />

      <div className="max-w-3xl mx-auto">
        {error && (
          <div className="mb-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg text-xs sm:text-sm">
            {error}
          </div>
        )}

        <div className="bg-white border rounded-2xl p-4 sm:p-6 shadow-sm">
          {/* Mode toggle — equal-width grid on mobile so both buttons
              share the row evenly. */}
          <div className="grid grid-cols-2 gap-2 mb-5">
            <button
              onClick={() => setMode('paste')}
              className={`px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition ${
                mode === 'paste'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              📝 {t('presPasteText')}
            </button>
            <button
              onClick={() => setMode('upload')}
              className={`px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition ${
                mode === 'upload'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              📎 {t('presUploadFile')}
            </button>
          </div>

          {/* Title hint — text-base on mobile prevents iOS auto-zoom. */}
          <label className="block text-xs sm:text-sm font-semibold text-gray-700 mb-2">
            🏷️ {t('presTitleOptional')}
          </label>
          <input
            type="text"
            value={titleHint}
            onChange={(e) => setTitleHint(e.target.value)}
            placeholder={t('presTitlePlaceholder')}
            className="w-full px-3 sm:px-4 py-2.5 border rounded-lg mb-4 text-base sm:text-sm"
          />

          {/* Paste mode */}
          {mode === 'paste' && (
            <>
              <label className="block text-xs sm:text-sm font-semibold text-gray-700 mb-2">
                📝 {t('presContent')}
              </label>
              <textarea
                value={contentText}
                onChange={(e) => setContentText(e.target.value)}
                placeholder={t('presContentPlaceholder')}
                rows="10"
                className="w-full px-3 sm:px-4 py-3 border rounded-lg mb-4 text-base sm:text-sm font-mono"
              />
            </>
          )}

          {/* Upload mode */}
          {mode === 'upload' && (
            <div className="mb-4">
              <label className="block w-full border-2 border-dashed border-gray-300 rounded-lg p-6 sm:p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,.md"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <p className="text-3xl sm:text-4xl mb-2">📎</p>
                <p className="text-xs sm:text-sm font-medium text-gray-700">
                  {loading ? '⏳ ' + t('chatUploading') : t('presClickUpload')}
                </p>
                <p className="text-[10px] sm:text-xs text-gray-500 mt-1">
                  {t('presSupportedFormats')}
                </p>
              </label>

              {fileName && (
                <div className="mt-3 px-4 py-2 bg-green-50 border border-green-200 rounded-lg text-xs sm:text-sm text-green-700">
                  ✅ {t('presLoaded')}: {fileName}
                </div>
              )}

              {contentText && (
                <>
                  <label className="block text-xs sm:text-sm font-semibold text-gray-700 mb-2 mt-4">
                    📝 {t('presExtracted')}
                  </label>
                  <textarea
                    value={contentText}
                    onChange={(e) => setContentText(e.target.value)}
                    rows="6"
                    className="w-full px-3 sm:px-4 py-3 border rounded-lg mb-2 text-base sm:text-sm font-mono"
                  />
                </>
              )}
            </div>
          )}

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={loading || !contentText.trim()}
            className="w-full px-4 sm:px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 font-medium shadow-sm transition text-sm"
          >
            {loading ? '⏳ ' + t('presGenerating') : '🎨 ' + t('presGenerate')}
          </button>
        </div>

        {/* Tip box */}
        <div className="mt-4 sm:mt-6 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-3 sm:p-4">
          <h3 className="text-xs sm:text-sm font-bold text-gray-800 mb-1">
            💡 {t('presHowItWorks')}
          </h3>
          <p className="text-xs sm:text-xs text-gray-600 leading-relaxed">
            {t('presHowItWorksDesc')}
          </p>
        </div>
      </div>
    </div>
  )
}

export default PresentationPage
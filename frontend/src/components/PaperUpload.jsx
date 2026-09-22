import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE } from '../api'

function PaperUpload({ onPaperLoaded }) {
  const { t, i18n } = useTranslation()
  const [mode, setMode] = useState('upload')
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  /**
   * Handle pasted text — sends to backend for AI title + section detection.
   */
  const handlePaste = async () => {
    if (!text.trim()) {
      setError(t('chatPasteEmpty'))
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_BASE}/upload/paste`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text }),
      })

      const data = await res.json()

      if (data.status === 'success') {
        onPaperLoaded({
          title: data.title || 'Untitled Text',
          abstract: data.abstract || text.slice(0, 1500),
          introduction: data.introduction || '',
          methodology: data.methodology || '',
          findings: data.findings || '',
          limitations: data.limitations || '',
          conclusion: data.conclusion || '',
          key_points: data.key_points || [],
          full_text: data.full_text || text,
          char_count: data.char_count || text.length,
          word_count: data.word_count || text.split(/\s+/).length,
          method: 'pasted',
          content_type: data.content_type || 'other',
          source: 'pasted',
        })
      } else {
        // Fallback: raw text
        onPaperLoaded({
          title: t('chatPastedTitle'),
          abstract: text.slice(0, 1500),
          introduction: '',
          methodology: '',
          findings: '',
          limitations: '',
          conclusion: '',
          key_points: [],
          full_text: text,
          char_count: text.length,
          word_count: text.split(/\s+/).length,
          method: 'pasted',
          content_type: 'other',
          source: 'pasted',
        })
      }

      setText('')
    } catch (err) {
      console.error('Paste failed:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handle PDF upload.
   */
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError(t('chatPdfOnly'))
      return
    }

    setLoading(true)
    setError('')

    try {
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

      onPaperLoaded({
        title: data.title || 'Untitled Paper',
        abstract: data.abstract || '',
        introduction: data.introduction || '',
        methodology: data.methodology || '',
        findings: data.findings || '',
        limitations: data.limitations || '',
        conclusion: data.conclusion || '',
        key_points: data.key_points || [],
        full_text: data.full_text || '',
        char_count: data.char_count || 0,
        word_count: data.word_count || 0,
        method: data.method || '',
        filename: data.filename || file.name,
        content_type: data.content_type || 'other',
        source: 'uploaded',
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white border rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        📄 {t('chatUploadPaper')}
      </h2>

      {/* Mode toggle */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setMode('upload')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            mode === 'upload'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          📎 {t('chatUploadPdf')}
        </button>
        <button
          onClick={() => setMode('paste')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            mode === 'paste'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          📝 {t('chatPasteText')}
        </button>
      </div>

      {error && (
        <div className="mb-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {mode === 'paste' && (
        <>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={t('chatPastePlaceholder')}
            rows="8"
            className="w-full px-4 py-2 border rounded-lg mb-3 font-mono text-sm"
          />
          <button
            onClick={handlePaste}
            disabled={!text.trim() || loading}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? t('chatUploading') : t('chatLoadPaper')}
          </button>
        </>
      )}

      {mode === 'upload' && (
        <label className="block w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="hidden"
          />
          <p className="text-4xl mb-2">📎</p>
          <p className="text-sm font-medium text-gray-700">
            {loading ? t('chatUploading') : t('chatClickToUpload')}
          </p>
          <p className="text-xs text-gray-500 mt-1">{t('chatPdfOnly')}</p>
        </label>
      )}
    </div>
  )
}

export default PaperUpload
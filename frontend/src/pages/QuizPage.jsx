import React, { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE } from '../api'
import QuizCard from '../components/QuizCard'
import QuizResult from '../components/QuizResult'
import QuizHistory from '../components/QuizHistory'

function QuizPage() {
  const { t, i18n } = useTranslation()

  // Input state
  const [mode, setMode] = useState('paste')
  const [contextText, setContextText] = useState('')
  const [numQuestions, setNumQuestions] = useState(5)
  const [source, setSource] = useState('pasted')
  const [fileName, setFileName] = useState('')

  // Loading & error
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Quiz state
  const [questions, setQuestions] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState([])
  const [showResult, setShowResult] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [finalScore, setFinalScore] = useState(null)

  // History sidebar
  const [showHistory, setShowHistory] = useState(false)
  const [historyKey, setHistoryKey] = useState(0)

  const fileInputRef = useRef(null)

  // ─────────────────────────────────────────────
  // On mount: reset to input view
  // ─────────────────────────────────────────────
  useEffect(() => {
    setQuestions([])
    setAnswers([])
    setCurrentIndex(0)
    setShowResult(false)
    setFinalScore(null)
    setCurrentSessionId(null)
  }, [])

  // Auto-save answers to backend as user progresses
  useEffect(() => {
    if (currentSessionId && answers.length > 0) {
      fetch(`${API_BASE}/quiz/history/${currentSessionId}/answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers }),
      }).catch((err) => console.error('Auto-save failed:', err))
    }
  }, [answers, currentSessionId])

  // ─────────────────────────────────────────────
  // PDF Upload handler
  // ─────────────────────────────────────────────
  const handlePdfUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported')
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

      const text = data.full_text || data.abstract || ''
      setContextText(text)
      setSource('uploaded')
      setFileName(file.name)
      setMode('paste')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // ─────────────────────────────────────────────
  // Start quiz
  // ─────────────────────────────────────────────
  const startQuiz = async () => {
    if (!contextText.trim()) {
      setError(t('quizContextRequired'))
      return
    }

    setLoading(true)
    setError('')
    setQuestions([])
    setAnswers([])
    setCurrentIndex(0)
    setShowResult(false)
    setFinalScore(null)

    try {
      const res = await fetch(`${API_BASE}/quiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context_text: contextText,
          num_questions: numQuestions,
          lang: i18n.language,
          source: source,
        }),
      })

      const data = await res.json()

      if (data.questions && data.questions.length > 0) {
        setQuestions(data.questions)
        setAnswers(new Array(data.questions.length).fill(null))
        setCurrentSessionId(data.session_id || null)
        setHistoryKey((k) => k + 1)
      } else {
        setError(data.error || t('quizGenerateFailed'))
      }
    } catch (err) {
      console.error('Quiz error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // ─────────────────────────────────────────────
  // Answer handling
  // ─────────────────────────────────────────────
  const handleAnswer = (optionIndex) => {
    const newAnswers = [...answers]
    newAnswers[currentIndex] = optionIndex
    setAnswers(newAnswers)
  }

  const goNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1)
    } else {
      finishQuiz()
    }
  }

  const goPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    }
  }

  // ─────────────────────────────────────────────
  // Finish quiz — save score
  // ─────────────────────────────────────────────
  const finishQuiz = async () => {
    const correctCount = questions.reduce((acc, q, idx) => {
      return acc + (answers[idx] === q.correct_index ? 1 : 0)
    }, 0)
    const total = questions.length
    const percentage = Math.round((correctCount / total) * 100)

    setFinalScore({
      correct: correctCount,
      total: total,
      percentage: percentage,
    })
    setShowResult(true)

    if (currentSessionId) {
      try {
        await fetch(`${API_BASE}/quiz/history/${currentSessionId}/score`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ correct: correctCount, total: total }),
        })
        setHistoryKey((k) => k + 1)
      } catch (err) {
        console.error('Score save failed:', err)
      }
    }
  }

  // ─────────────────────────────────────────────
  // Restart — go back to input view
  // ─────────────────────────────────────────────
  const restartQuiz = () => {
    setQuestions([])
    setAnswers([])
    setCurrentIndex(0)
    setShowResult(false)
    setFinalScore(null)
    setCurrentSessionId(null)
    setError('')
    setContextText('')
    setFileName('')
    setSource('pasted')
    setMode('paste')
  }

  // ─────────────────────────────────────────────
  // Load a session from history
  // ─────────────────────────────────────────────
  const handleSelectSession = async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE}/quiz/history/${sessionId}`)
      const session = await res.json()

      if (!session || !session.questions) {
        setError('Failed to load session')
        return
      }

      setQuestions(session.questions)
      setAnswers(session.answers || new Array(session.questions.length).fill(null))
      setCurrentIndex(0)
      setShowResult(session.completed || false)
      setCurrentSessionId(session.id)
      setFinalScore(session.score || null)
      setContextText(session.content || '')
      setSource(session.source || 'pasted')
      setNumQuestions(session.num_questions || session.questions.length)
      setError('')

      if (window.innerWidth < 1024) {
        setShowHistory(false)
      }
    } catch (err) {
      console.error('Load session failed:', err)
      setError('Failed to load session')
    }
  }

  // ─────────────────────────────────────────────
  // HISTORY SIDEBAR COMPONENT (Reusable)
  // ─────────────────────────────────────────────
  const HistorySidebar = () => (
    <>
      <div
        className={`fixed top-0 right-0 h-screen w-full sm:w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
          showHistory ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <h3 className="font-bold text-gray-800 text-base sm:text-sm">
            📚 Quiz History
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
          style={{ height: 'calc(100vh - 64px)' }}
        >
          <QuizHistory
            refreshKey={historyKey}
            onSelectSession={handleSelectSession}
          />
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
  // VIEW 1: INPUT VIEW (no quiz started)
  // ═══════════════════════════════════════════════
  if (questions.length === 0) {
    return (
      <div className="px-4 py-4 sm:px-6 sm:py-6 max-w-7xl mx-auto relative">
        <div className="mb-4 sm:mb-6 flex items-center justify-between flex-wrap gap-2 sm:gap-3">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-800">
              🎯 {t('navQuiz')}
            </h1>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">
              {t('quizPageSubtitle')}
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
            📚 Quiz History
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
            {/* Mode toggle — equal-width grid on mobile */}
            <div className="grid grid-cols-2 gap-2 mb-5">
              <button
                onClick={() => setMode('paste')}
                className={`px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition ${
                  mode === 'paste'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                📝 {t('chatPasteText')}
              </button>
              <button
                onClick={() => setMode('upload')}
                className={`px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition ${
                  mode === 'upload'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                📎 {t('chatUploadPdf')}
              </button>
            </div>

            {/* Paste mode — text-base on mobile prevents iOS auto-zoom */}
            {mode === 'paste' && (
              <>
                <label className="block text-xs sm:text-sm font-semibold text-gray-700 mb-2">
                  📝 {t('quizPasteText')}
                </label>
                <textarea
                  value={contextText}
                  onChange={(e) => {
                    setContextText(e.target.value)
                    setSource('pasted')
                  }}
                  placeholder={t('quizPastePlaceholder')}
                  rows="12"
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
                    accept=".pdf"
                    onChange={handlePdfUpload}
                    className="hidden"
                  />
                  <p className="text-3xl sm:text-4xl mb-2">📎</p>
                  <p className="text-xs sm:text-sm font-medium text-gray-700">
                    {loading
                      ? '⏳ ' + t('chatUploading')
                      : t('chatClickToUpload')}
                  </p>
                  <p className="text-[10px] sm:text-xs text-gray-500 mt-1">
                    {t('chatPdfOnly')}
                  </p>
                </label>

                {fileName && (
                  <div className="mt-3 px-4 py-2 bg-green-50 border border-green-200 rounded-lg text-xs sm:text-sm text-green-700">
                    ✅ Loaded: {fileName}
                  </div>
                )}
              </div>
            )}

            {/* Number of questions — wraps on mobile if needed */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-4 mb-4">
              <label className="text-xs sm:text-sm font-semibold text-gray-700">
                {t('quizNumQuestions')}:
              </label>
              <select
                value={numQuestions}
                onChange={(e) => setNumQuestions(Number(e.target.value))}
                className="px-3 py-1.5 border rounded-lg text-base sm:text-sm bg-white cursor-pointer"
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={15}>15</option>
                <option value={20}>20</option>
                <option value={30}>30</option>
                <option value={50}>50</option>
              </select>
              <span className="text-[11px] sm:text-xs text-gray-500">
                (max 50)
              </span>
            </div>

            {/* Generate button */}
            <button
              onClick={startQuiz}
              disabled={loading || !contextText.trim()}
              className="w-full px-4 sm:px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 font-medium shadow-sm transition text-sm"
            >
              {loading
                ? '⏳ ' + t('quizGenerating')
                : '🎯 ' + t('quizGenerate')}
            </button>
          </div>

          <div className="mt-4 sm:mt-6 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-3 sm:p-4">
            <h3 className="text-xs sm:text-sm font-bold text-gray-800 mb-1">
              💡 {t('quizQuickTip')}
            </h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              {t('quizQuickTipDesc')}
            </p>
          </div>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════════════
  // VIEW 2: RESULT VIEW
  // ═══════════════════════════════════════════════
  if (showResult && finalScore) {
    return (
      <div className="px-4 py-4 sm:px-6 sm:py-6 max-w-3xl mx-auto relative">
        <div className="mb-4 flex items-center justify-between flex-wrap gap-2">
          <h1 className="text-lg sm:text-xl font-bold text-gray-800">
            🎯 {t('quizResults')}
          </h1>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 hover:border-blue-400 transition"
          >
            📚 History
          </button>
        </div>

        <QuizResult
          questions={questions}
          answers={answers}
          score={finalScore}
          onRestart={restartQuiz}
          onViewHistory={() => setShowHistory(true)}
        />

        <HistorySidebar />
      </div>
    )
  }

  // ═══════════════════════════════════════════════
  // VIEW 3: QUESTION VIEW
  // ═══════════════════════════════════════════════
  const currentQuestion = questions[currentIndex]
  const isAnswered =
    answers[currentIndex] !== null && answers[currentIndex] !== undefined
  const isLastQuestion = currentIndex === questions.length - 1

  return (
    <div className="px-4 py-4 sm:px-6 sm:py-6 max-w-3xl mx-auto">
      {/* Progress bar */}
      <div className="mb-4 sm:mb-6">
        <div className="flex justify-between text-xs text-gray-600 mb-2">
          <span>
            {t('quizProgress')}: {currentIndex + 1}/{questions.length}
          </span>
          <span>
            {Math.round(((currentIndex + 1) / questions.length) * 100)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-blue-500 h-full transition-all duration-300"
            style={{
              width: `${((currentIndex + 1) / questions.length) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Question card */}
      <QuizCard
        question={currentQuestion}
        index={currentIndex}
        total={questions.length}
        selectedIndex={answers[currentIndex]}
        onSelect={handleAnswer}
      />

      {/* Navigation — buttons share the row, thumb-friendly height on mobile */}
      <div className="mt-4 sm:mt-6 flex justify-between items-center gap-2">
        <button
          onClick={goPrev}
          disabled={currentIndex === 0}
          className="px-3 sm:px-5 py-2.5 text-xs sm:text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition"
        >
          ← {t('quizPrev')}
        </button>

        <button
          onClick={goNext}
          disabled={!isAnswered}
          className="px-4 sm:px-6 py-2.5 text-xs sm:text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:opacity-40 shadow-sm transition"
        >
          {isLastQuestion ? '📊 ' + t('quizSeeResult') : t('quizNext') + ' →'}
        </button>
      </div>
    </div>
  )
}

export default QuizPage
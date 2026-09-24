import React, { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE, REVIEW_ENDPOINTS } from '../api'
import PaperChat from '../components/PaperChat'
import QuizGenerator from '../components/QuizGenerator'
import ProgressTracker from '../components/ProgressTracker'
import ReviewHistory from '../components/ReviewHistory'

function ReviewPage() {
  const { t, i18n } = useTranslation()

  const [keyword, setKeyword] = useState('')
  const [criteria, setCriteria] = useState('')
  const [papers, setPapers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [duplicatesRemoved, setDuplicatesRemoved] = useState(0)
  const [selectedPaper, setSelectedPaper] = useState(null)
  const [pipelineCounts, setPipelineCounts] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [filterDecision, setFilterDecision] = useState('all')
  const pollRef = useRef(null)

  // ─── Review History state ───
  const [showHistory, setShowHistory] = useState(false)
  const [historyKey, setHistoryKey] = useState(0)
  const [currentSessionId, setCurrentSessionId] = useState(null)

  const criteriaOptions = [
    { value: '', label: 'Select criteria...' },
    { value: '2020+ studies', label: '2020+ studies (Recent only)' },
    { value: '2022+ studies', label: '2022+ studies (Very recent)' },
    { value: '2020+ empirical studies', label: '2020+ empirical studies' },
    { value: '2020+ peer-reviewed studies', label: '2020+ peer-reviewed only' },
    { value: '2020+ English language studies', label: '2020+ English only' },
    { value: '2020+ studies with empirical data', label: '2020+ with empirical data' },
    { value: 'custom', label: '✏️ Custom (write manually)' },
  ]

  const [criteriaMode, setCriteriaMode] = useState('dropdown')

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const handleCriteriaSelect = (e) => {
    const value = e.target.value
    if (value === 'custom') {
      setCriteriaMode('custom')
      setCriteria('')
    } else {
      setCriteriaMode('dropdown')
      setCriteria(value)
    }
  }

  // ═══════════════════════════════════════════════
  // Auto-save session after pipeline completes
  // ═══════════════════════════════════════════════
  const saveSessionToHistory = async (papersList, duplicates, counts, kw, cr, lang) => {
    if (!papersList || papersList.length === 0) return
    try {
      const res = await fetch(REVIEW_ENDPOINTS.save, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyword: kw,
          criteria: cr,
          lang: lang,
          papers: papersList,
          duplicates_removed: duplicates || 0,
          counts: counts || {},
          report_filename: null,
        }),
      })
      const data = await res.json()
      if (data.status === 'success') {
        setCurrentSessionId(data.session_id)
        setHistoryKey((k) => k + 1)
      }
    } catch (err) {
      console.error('[ReviewHistory] Auto-save failed:', err)
    }
  }

  // ═══════════════════════════════════════════════
  // Load a session from history
  // ═══════════════════════════════════════════════
  const handleSelectSession = async (sessionId) => {
    try {
      const res = await fetch(REVIEW_ENDPOINTS.session(sessionId))
      const data = await res.json()
      if (data.status !== 'success') {
        setError(data.detail || 'Failed to load session')
        return
      }

      setKeyword(data.keyword || '')
      setCriteria(data.criteria || '')
      setCriteriaMode('dropdown')
      setPapers(data.papers || [])
      setDuplicatesRemoved(data.duplicates_removed || 0)
      setPipelineCounts(data.counts || null)
      setCurrentSessionId(data.session_id)
      setSelectedPaper(null)
      setFilterDecision('all')
      setJobStatus(null)
      setError('')

      if (window.innerWidth < 1024) {
        setShowHistory(false)
      }
    } catch (err) {
      console.error('[ReviewHistory] Load session failed:', err)
      setError('Failed to load session')
    }
  }

  const runPipeline = async () => {
    if (!keyword.trim() || !criteria.trim()) {
      setError(t('keywordCriteriaRequired'))
      return
    }

    setLoading(true)
    setError('')
    setPapers([])
    setDuplicatesRemoved(0)
    setPipelineCounts(null)

    setJobStatus({
      status: 'starting',
      stage_label: t('startingPipeline'),
      elapsed: 0,
      progress_current: 0,
      progress_total: 0,
    })

    try {
      const startRes = await fetch(`${API_BASE}/pipeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword, criteria, lang: i18n.language }),
      })

      if (!startRes.ok) throw new Error(`Pipeline failed: ${startRes.status}`)
      const { job_id } = await startRes.json()

      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_BASE}/pipeline/status/${job_id}`)
          const status = await statusRes.json()
          setJobStatus(status)

          if (status.status === 'complete' || status.status === 'failed') {
            clearInterval(pollRef.current)
            pollRef.current = null
            setLoading(false)

            if (status.status === 'complete' && status.result) {
              const resultPapers = status.result.papers || []
              const resultDups = status.result.duplicates_removed || 0
              const resultCounts = status.result.counts || null

              setPapers(resultPapers)
              setDuplicatesRemoved(resultDups)
              setPipelineCounts(resultCounts)

              await saveSessionToHistory(
                resultPapers,
                resultDups,
                resultCounts,
                keyword,
                criteria,
                i18n.language
              )
            } else if (status.status === 'failed') {
              setError(status.error || t('pipelineFailed'))
            }
          }
        } catch (pollErr) {
          console.error('Poll error:', pollErr)
        }
      }, 1000)
    } catch (err) {
      setError(err.message)
      setLoading(false)
      setJobStatus({
        status: 'failed',
        stage_label: t('pipelineFailed'),
        elapsed: 0,
        error: String(err),
      })
    }
  }

  const downloadReport = async () => {
    const included = papers.filter((p) => p.decision === 'Include')

    if (included.length === 0) {
      setError(t('needIncludedPaper'))
      return
    }

    const fallbackCounts = {
      total_found: papers.length,
      duplicates_removed: duplicatesRemoved || 0,
      irrelevant_excluded: papers.filter((p) => p.decision === 'Exclude').length,
      maybe: papers.filter((p) => p.decision === 'Maybe').length,
      error: papers.filter((p) => p.decision === 'Error').length,
      total_included: included.length,
    }

    const counts =
      pipelineCounts && pipelineCounts.total_found > 0
        ? pipelineCounts
        : fallbackCounts

    try {
      setError('')
      const res = await fetch(`${API_BASE}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          papers: included,
          keyword: keyword,
          criteria: criteria,
          lang: i18n.language,
          prisma_counts: {
            identified: counts.total_found || 0,
            duplicates_removed: counts.duplicates_removed || 0,
            screened: (counts.total_found || 0) - (counts.duplicates_removed || 0),
            excluded: counts.irrelevant_excluded || 0,
            maybe: counts.maybe || 0,
            error: counts.error || 0,
            full_text: counts.total_included || included.length,
            included: counts.total_included || included.length,
          },
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Report failed: ${res.status}`)
      }

      const data = await res.json()
      if (data.status !== 'success') {
        throw new Error(data.message || 'Report generation failed')
      }

      if (currentSessionId && data.filename) {
        try {
          await fetch(REVIEW_ENDPOINTS.attachReport(currentSessionId), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ report_filename: data.filename }),
          })
          setHistoryKey((k) => k + 1)
        } catch (attachErr) {
          console.error('[ReviewHistory] Attach report failed:', attachErr)
        }
      }

      window.open(`${API_BASE}/download/${data.filename}`, '_blank')
    } catch (err) {
      console.error('[Report] Error:', err)
      setError(`Report download failed: ${err.message}`)
    }
  }

  const decisionColor = (decision) => {
    if (decision === 'Include') return 'bg-green-100 text-green-800'
    if (decision === 'Exclude') return 'bg-red-100 text-red-800'
    if (decision === 'Maybe') return 'bg-yellow-100 text-yellow-800'
    return 'bg-gray-100 text-gray-600'
  }

  // ═══════════════════════════════════════════════
  // Source badge — supports all 4 sources
  // ═══════════════════════════════════════════════
  const sourceColor = (source) => {
    if (source === 'arxiv') return 'bg-red-100 text-red-800'
    if (source === 'crossref') return 'bg-emerald-100 text-emerald-800'
    if (source === 'openalex') return 'bg-purple-100 text-purple-800'
    if (source === 'semantic_scholar') return 'bg-blue-100 text-blue-800'
    return 'bg-gray-100 text-gray-600'
  }

  const sourceLabel = (source) => {
    if (source === 'arxiv') return 'arXiv'
    if (source === 'crossref') return 'CR'
    if (source === 'openalex') return 'OA'
    if (source === 'semantic_scholar') return 'SS'
    return '—'
  }

  const getLink = (paper) => {
    if (paper.doi) return `https://doi.org/${paper.doi}`
    return paper.url || paper.verification_url || ''
  }

  const confidenceColor = (conf) => {
    if (conf >= 80) return 'text-green-600'
    if (conf >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const filteredPapers =
    filterDecision === 'all'
      ? papers
      : papers.filter((p) => p.decision === filterDecision)

  const decisionCounts = {
    all: papers.length,
    Include: papers.filter((p) => p.decision === 'Include').length,
    Exclude: papers.filter((p) => p.decision === 'Exclude').length,
    Maybe: papers.filter((p) => p.decision === 'Maybe').length,
  }

  // ═══════════════════════════════════════════════
  // Sidebar (mobile-responsive)
  // ═══════════════════════════════════════════════
  const HistorySidebar = () => (
    <>
      <div
        className={`fixed top-0 right-0 h-screen w-full sm:w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
          showHistory ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <h3 className="font-bold text-gray-800 text-sm">
            📚 Review History
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
          <ReviewHistory
            refreshKey={historyKey}
            onSelectSession={handleSelectSession}
            activeSessionId={currentSessionId}
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

  return (
    <div className="p-3 sm:p-6 max-w-7xl mx-auto relative">
      {/* ─── Header with History button ─── */}
      <div className="mb-4 sm:mb-6 flex items-center justify-between flex-wrap gap-2 sm:gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-800">
            📚 {t('navReview')}
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            {t('reviewPageSubtitle')}
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
          📚 History
          <span className="text-xs opacity-70">
            {showHistory ? '✕' : '→'}
          </span>
        </button>
      </div>

      <HistorySidebar />

      {error && (
        <div className="mb-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="mb-4 bg-white p-3 sm:p-4 rounded-lg border">
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder={t('searchPlaceholder')}
          className="w-full px-3 sm:px-4 py-2 border rounded-lg mb-3 text-sm"
        />

        {criteriaMode === 'dropdown' ? (
          <div className="relative mb-3">
            <select
              value={criteria}
              onChange={handleCriteriaSelect}
              className="w-full px-3 sm:px-4 py-2 border rounded-lg bg-white cursor-pointer appearance-none pr-10 text-sm"
            >
              {criteriaOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <span className="absolute right-3 top-2.5 text-gray-400 pointer-events-none">
              ▼
            </span>
          </div>
        ) : (
          <div className="mb-3">
            <textarea
              value={criteria}
              onChange={(e) => setCriteria(e.target.value)}
              placeholder={t('criteriaPlaceholder')}
              rows="3"
              className="w-full px-3 sm:px-4 py-2 border rounded-lg mb-2 text-sm"
              autoFocus
            />
            <button
              onClick={() => {
                setCriteriaMode('dropdown')
                setCriteria('')
              }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-lg border border-gray-300 transition shadow-sm"
            >
              <span>←</span>
              <span>Back to Dropdown</span>
            </button>
          </div>
        )}

        {/* Buttons — stack on mobile */}
        <div className="flex flex-col sm:flex-row gap-2 mt-3">
          <button
            onClick={runPipeline}
            disabled={loading}
            className="flex-1 px-4 sm:px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 font-medium text-sm"
          >
            {loading ? '⏳ Running...' : t('runPipeline')}
          </button>
          <button
            onClick={downloadReport}
            disabled={!papers.some((p) => p.decision === 'Include')}
            className="px-4 sm:px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 font-medium text-sm"
          >
            {t('downloadReport')}
          </button>
        </div>

        {duplicatesRemoved > 0 && (
          <p className="text-xs text-gray-500 mt-2">
            ✅ {duplicatesRemoved} {t('duplicatesRemoved')}
          </p>
        )}
      </div>

      {jobStatus && (
        <div className="mb-6 flex justify-center">
          <div className="w-full max-w-3xl">
            <ProgressTracker status={jobStatus} />
          </div>
        </div>
      )}

      {papers.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2 items-center">
          <span className="text-xs sm:text-sm text-gray-600 font-medium">
            Filter:
          </span>
          {['all', 'Include', 'Exclude', 'Maybe'].map((f) => (
            <button
              key={f}
              onClick={() => setFilterDecision(f)}
              className={`px-2.5 sm:px-3 py-1 rounded-full text-xs font-medium transition ${
                filterDecision === f
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {f === 'all' ? 'All' : f} ({decisionCounts[f]})
            </button>
          ))}
        </div>
      )}

      {/* Results table — horizontally scrollable on mobile */}
      <div className="overflow-x-auto mb-4 sm:mb-6 -mx-3 sm:mx-0 px-3 sm:px-0">
        <table className="min-w-full bg-white border rounded-lg text-xs sm:text-sm">
          <thead>
            <tr className="bg-gray-200 text-xs uppercase">
              <th className="px-2 py-2 text-left">#</th>
              <th className="px-2 py-2 text-left">{t('colStudy')}</th>
              <th className="px-2 py-2 text-left">{t('year')}</th>
              <th className="px-2 py-2 text-left">{t('colSource')}</th>
              <th className="px-2 py-2 text-left">{t('colLink')}</th>
              <th className="px-2 py-2 text-left">{t('confidence')}</th>
              <th className="px-2 py-2 text-left">{t('decision')}</th>
            </tr>
          </thead>
          <tbody>
            {filteredPapers.map((paper, idx) => (
              <tr key={idx} className="border-t hover:bg-gray-50">
                <td className="px-2 py-2 text-xs text-gray-500 align-top">
                  {idx + 1}
                </td>
                <td
                  className="px-2 py-2 cursor-pointer align-top"
                  onClick={() => setSelectedPaper(paper)}
                >
                  <div className="text-xs sm:text-sm font-medium text-gray-800">
                    {paper.title}
                  </div>
                  <div className="text-[10px] sm:text-xs text-gray-500 mt-1">
                    {paper.authors}
                  </div>
                </td>
                <td className="px-2 py-2 text-xs text-gray-600 align-top">
                  {paper.year}
                </td>
                <td className="px-2 py-2 align-top">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${sourceColor(
                      paper.source_api
                    )}`}
                  >
                    {sourceLabel(paper.source_api)}
                  </span>
                </td>
                <td className="px-2 py-2 align-top">
                  {getLink(paper) ? (
                    <a
                      href={getLink(paper)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-xs whitespace-nowrap"
                    >
                      🔗 DOI
                    </a>
                  ) : (
                    <span className="text-gray-400 text-xs">—</span>
                  )}
                </td>
                <td className="px-2 py-2 align-top">
                  <span
                    className={`text-xs font-semibold ${confidenceColor(
                      paper.confidence || 0
                    )}`}
                  >
                    {paper.confidence || 0}%
                  </span>
                </td>
                <td className="px-2 py-2 align-top">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${decisionColor(
                      paper.decision
                    )}`}
                  >
                    {paper.decision || 'Pending'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {papers.length === 0 && (
          <p className="text-center text-gray-500 py-6 text-sm">
            {t('noPapers')}
          </p>
        )}
      </div>

      {selectedPaper && (
        <div className="space-y-4 bg-white p-3 sm:p-4 rounded-lg border">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="text-xs sm:text-sm font-semibold text-gray-800">
                {selectedPaper.title}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {selectedPaper.authors} ({selectedPaper.year})
              </p>
              {getLink(selectedPaper) && (
                <a
                  href={getLink(selectedPaper)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline break-all"
                >
                  🔗 {getLink(selectedPaper)}
                </a>
              )}
            </div>
            <button
              onClick={() => setSelectedPaper(null)}
              className="text-gray-400 hover:text-red-500 text-sm flex-shrink-0"
            >
              ✕
            </button>
          </div>
          <PaperChat contextText={selectedPaper.abstract} />
          <QuizGenerator contextText={selectedPaper.abstract} />
        </div>
      )}
    </div>
  )
}

export default ReviewPage
import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, LineChart, Line,
  ResponsiveContainer,
} from 'recharts'
import { API_BASE } from '../api'

// ─── Colors matching website theme ───
const COLORS = {
  blue: '#2563eb',
  green: '#16a34a',
  red: '#dc2626',
  yellow: '#eab308',
  purple: '#9333ea',
  indigo: '#6366f1',
  cyan: '#06b6d4',
}

const DECISION_COLORS = {
  Include: COLORS.green,
  Exclude: COLORS.red,
  Maybe: COLORS.yellow,
}

function StatisticsPage() {
  const { t } = useTranslation()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/stats/summary`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStats(data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="inline-block animate-spin text-4xl">⚙️</div>
        <p className="mt-2 text-gray-500">{t('statsLoading')}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-500">
          {t('statsError')}: {error}
        </p>
        <button
          onClick={fetchStats}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg"
        >
          {t('statsRetry')}
        </button>
      </div>
    )
  }

  if (!stats) return null

  const { overview, decisions, papers_by_year, quiz_scores, activity, top_keywords } = stats

  // Prepare pie data
  const pieData = Object.entries(decisions)
    .map(([name, value]) => ({ name, value }))
    .filter((d) => d.value > 0)

  // Translate decision names for display
  const translateDecision = (name) => {
    if (name === 'Include') return t('statsDecisionInclude')
    if (name === 'Exclude') return t('statsDecisionExclude')
    if (name === 'Maybe') return t('statsDecisionMaybe')
    return name
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            📊 {t('statsTitle')}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {t('statsSubtitle')}
          </p>
        </div>

        <button
          onClick={fetchStats}
          className="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 bg-white text-gray-700 hover:border-blue-400 transition"
        >
          🔄 {t('statsRefresh')}
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        <StatCard icon="📚" label={t('statsReviews')} value={overview.reviews} color="blue" />
        <StatCard icon="💬" label={t('statsChats')} value={overview.chats} color="purple" />
        <StatCard icon="🎯" label={t('statsQuizzes')} value={overview.quizzes} color="green" />
        <StatCard icon="🎨" label={t('statsPresentations')} value={overview.presentations} color="indigo" />
        <StatCard icon="📄" label={t('statsTotalPapers')} value={overview.total_papers} color="cyan" />
        <StatCard icon="✅" label={t('statsIncluded')} value={overview.total_included} color="green" />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Decision Distribution — Pie */}
        <ChartCard title={t('statsDecisionDistribution')} icon="🥧">
          {pieData.length === 0 ? (
            <EmptyState text={t('statsNoReviewData')} hint={t('statsEmptyHint')} />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  label={({ name, value }) => `${translateDecision(name)}: ${value}`}
                  outerRadius={90}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, idx) => (
                    <Cell
                      key={idx}
                      fill={DECISION_COLORS[entry.name] || COLORS.blue}
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name) => [value, translateDecision(name)]} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Papers by Year — Bar */}
        <ChartCard title={t('statsPapersByYear')} icon="📅">
          {papers_by_year.length === 0 ? (
            <EmptyState text={t('statsNoPaperData')} hint={t('statsEmptyHint')} />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={papers_by_year}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" fontSize={11} interval="preserveStartEnd" />
                <YAxis fontSize={12} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill={COLORS.blue} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Quiz Score Trend — Line */}
        <ChartCard title={t('statsQuizTrend')} icon="📈">
          {quiz_scores.history.length === 0 ? (
            <EmptyState text={t('statsNoQuizData')} hint={t('statsEmptyHint')} />
          ) : (
            <>
              <div className="mb-2 text-center">
                <span className="text-sm text-gray-500">
                  {t('statsAverage')}:{' '}
                </span>
                <span className="text-lg font-bold text-green-600">
                  {quiz_scores.average}%
                </span>
                <span className="text-xs text-gray-400 ml-2">
                  ({quiz_scores.total} {t('statsQuizzes')})
                </span>
              </div>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={quiz_scores.history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" fontSize={11} />
                  <YAxis domain={[0, 100]} fontSize={12} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="percentage"
                    stroke={COLORS.green}
                    strokeWidth={3}
                    dot={{ fill: COLORS.green, r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </>
          )}
        </ChartCard>

        {/* Session Activity — Bar */}
        <ChartCard title={t('statsActivity')} icon="🔥">
          {activity.length === 0 ? (
            <EmptyState text={t('statsNoActivity')} hint={t('statsEmptyHint')} />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={activity}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  fontSize={10}
                  interval={4}
                  tickFormatter={(d) => (d ? d.slice(5) : '')}
                />
                <YAxis fontSize={12} allowDecimals={false} />
                <Tooltip />
                <Bar
                  dataKey="count"
                  fill={COLORS.indigo}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Top Keywords */}
      <ChartCard title={t('statsTopKeywords')} icon="🏆">
        {top_keywords.length === 0 ? (
          <EmptyState text={t('statsNoKeywordData')} hint={t('statsEmptyHint')} />
        ) : (
          <div className="space-y-2">
            {top_keywords.map((kw, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50"
              >
                <span className="text-sm font-bold text-gray-400 w-6">
                  #{idx + 1}
                </span>
                <span className="flex-1 text-sm text-gray-700 truncate">
                  {kw.keyword}
                </span>
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-medium">
                  {kw.count}{' '}
                  {kw.count === 1 ? t('statsSearch') : t('statsSearches')}
                </span>
              </div>
            ))}
          </div>
        )}
      </ChartCard>
    </div>
  )
}

// ─── Reusable components ───

function StatCard({ icon, label, value, color = 'blue' }) {
  const colorClass =
    {
      blue: 'border-blue-200 bg-blue-50 text-blue-700',
      green: 'border-green-200 bg-green-50 text-green-700',
      red: 'border-red-200 bg-red-50 text-red-700',
      purple: 'border-purple-200 bg-purple-50 text-purple-700',
      indigo: 'border-indigo-200 bg-indigo-50 text-indigo-700',
      cyan: 'border-cyan-200 bg-cyan-50 text-cyan-700',
    }[color] || 'border-gray-200 bg-gray-50 text-gray-700'

  return (
    <div className={`border-2 rounded-xl p-3 text-center ${colorClass}`}>
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-[11px] font-medium opacity-80">{label}</div>
    </div>
  )
}

function ChartCard({ title, icon, children }) {
  return (
    <div className="bg-white border rounded-2xl p-5 shadow-sm">
      <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
        <span>{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  )
}

function EmptyState({ text, hint }) {
  return (
    <div className="text-center text-sm text-gray-400 py-12">
      {text}
      {hint && <div className="text-xs mt-1">{hint}</div>}
    </div>
  )
}

export default StatisticsPage
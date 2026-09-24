import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

/**
 * How It Works Page — explains the full ReviewMind pipeline.
 * Uses 7 step cards + tool explanations + feature highlights + tech stack.
 */
function HowItWorks() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [activeStep, setActiveStep] = useState(0)
  const [activeTool, setActiveTool] = useState(0)

  // 7-step pipeline
  const steps = [
    {
      id: 1,
      icon: '🔍',
      title: t('howStep1Title') || 'Search Papers',
      short: t('howStep1Short') || 'Fetch from APIs',
      description: t('howStep1Desc') || 'Enter your research topic. ReviewMind queries Semantic Scholar and OpenAlex APIs to fetch the most relevant papers automatically.',
      tech: 'Semantic Scholar API • OpenAlex API',
      color: 'blue',
    },
    {
      id: 2,
      icon: '🧹',
      title: t('howStep2Title') || 'Remove Duplicates',
      short: t('howStep2Short') || 'ML Deduplication',
      description: t('howStep2Desc') || 'Machine Learning (TF-IDF + Cosine Similarity) detects and removes duplicate papers so you only review unique studies.',
      tech: 'scikit-learn • TF-IDF • Cosine Similarity',
      color: 'purple',
    },
    {
      id: 3,
      icon: '🤖',
      title: t('howStep3Title') || 'AI Screening',
      short: t('howStep3Short') || 'Include / Exclude',
      description: t('howStep3Desc') || 'Google Gemini AI reads each paper abstract and classifies it as Include, Exclude, or Maybe based on your criteria.',
      tech: 'Google Gemini 2.5 • Multi-Agent AI',
      color: 'green',
    },
    {
      id: 4,
      icon: '✅',
      title: t('howStep4Title') || 'Quality Check',
      short: t('howStep4Short') || 'Second AI Pass',
      description: t('howStep4Desc') || 'A second AI agent independently reviews each screening decision, agreeing or overriding with confidence scores.',
      tech: 'Quality-Check Agent • Confidence Scoring',
      color: 'yellow',
    },
    {
      id: 5,
      icon: '📊',
      title: t('howStep5Title') || 'Extract Data',
      short: t('howStep5Short') || 'Structured Info',
      description: t('howStep5Desc') || 'From each included paper, AI extracts methodology, sample size, key findings, and limitations into a structured table.',
      tech: 'Gemini Extraction Agent • JSON Output',
      color: 'indigo',
    },
    {
      id: 6,
      icon: '📄',
      title: t('howStep6Title') || 'Generate Report',
      short: t('howStep6Short') || 'Word + PRISMA',
      description: t('howStep6Desc') || 'Download a professional Word report with 6 tables, PRISMA flow diagram, and APA references — all automatically generated.',
      tech: 'python-docx • matplotlib • PRISMA Standard',
      color: 'red',
    },
    {
      id: 7,
      icon: '🔗',
      title: t('howStep7Title') || 'Verify Sources',
      short: t('howStep7Short') || 'DOI + API Logs',
      description: t('howStep7Desc') || 'Every paper carries its DOI link, API source, semantic ID, and fetched timestamp. Judges can independently verify each source.',
      tech: 'DOI Links • API Endpoints • Timestamps',
      color: 'pink',
    },
  ]

  // Companion Tools
  const tools = [
    {
      key: 'chat',
      icon: '💬',
      name: 'Chat with Papers',
      tagline: 'Ask anything about any paper — instantly',
      accent: 'blue',
      steps: [
        { icon: '📥', title: 'Provide Content', desc: 'Upload a PDF or paste raw text (abstract, full paper, notes) — no length limit.' },
        { icon: '🧠', title: 'AI Reads Everything', desc: 'Gemini reads the full content and builds a working memory of the paper.' },
        { icon: '❓', title: 'Ask Any Question', desc: 'Ask in English or Bengali — about methods, results, limitations, anything.' },
        { icon: '💡', title: 'Grounded Answer', desc: 'AI answers only from the provided text. If the answer is not there, it says so.' },
        { icon: '📚', title: 'History Sidebar', desc: 'Every chat is saved. Reload, rename, or delete any past conversation.' },
      ],
    },
    {
      key: 'quiz',
      icon: '🎯',
      name: 'Quiz Mode',
      tagline: 'Test your understanding of any paper',
      accent: 'green',
      steps: [
        { icon: '📥', title: 'Provide Content', desc: 'Paste text or upload a PDF — same input as Chat.' },
        { icon: '⚙️', title: 'Choose Question Count', desc: 'Select 5, 10, 15, 20, 30, or 50 multiple-choice questions.' },
        { icon: '🤖', title: 'AI Generates MCQs', desc: 'Gemini creates 4-option questions with correct answers and explanations.' },
        { icon: '✍️', title: 'Take the Quiz', desc: 'Answer one by one with live progress tracking. Auto-save as you go.' },
        { icon: '📊', title: 'Score & Review', desc: 'See your percentage, correct/wrong counts, and review each answer with explanations.' },
        { icon: '📚', title: 'Quiz History', desc: 'All sessions saved. Reload past quizzes, rename them, resume where you left off.' },
      ],
    },
    {
      key: 'presentation',
      icon: '🎨',
      name: 'Presentation Maker',
      tagline: 'Any content → ready-to-present slides',
      accent: 'purple',
      steps: [
        { icon: '📥', title: 'Provide Content', desc: 'Paste any text, or upload a PDF / TXT / MD file. Not restricted to research papers.' },
        { icon: '🏷️', title: 'Optional Title', desc: 'Give the deck a custom title, or let AI decide one from your content.' },
        { icon: '🤖', title: 'AI Structures Slides', desc: 'Gemini designs 8–15 slides, each with a clear title and 3–6 bullet points.' },
        { icon: '👁️', title: 'Preview Slides', desc: 'Navigate slide-by-slide with prev/next buttons and dot indicators.' },
        { icon: '⬇️', title: 'Download Both', desc: 'Get a PowerPoint (.pptx) AND a PDF version — blue theme matching the site.' },
        { icon: '📚', title: 'Presentation History', desc: 'Every deck is saved. Reload, rename, download again, or delete anytime.' },
      ],
    },
  ]

  // Feature highlights
  const features = [
    {
      icon: '🌐',
      title: t('howFeatureBilingual') || 'Bilingual',
      desc: t('howFeatureBilingualDesc') || 'Full support for English and Bengali',
    },
    {
      icon: '🔍',
      title: t('howFeatureSource') || 'Traceable Sources',
      desc: t('howFeatureSourceDesc') || 'Every paper has a DOI and API log',
    },
    {
      icon: '⚡',
      title: t('howFeatureRealtime') || 'Real-Time Progress',
      desc: t('howFeatureRealtimeDesc') || 'Live pipeline tracking with stage-by-stage updates',
    },
    {
      icon: '🤖',
      title: t('howFeatureMultiAgent') || 'Multi-Agent AI',
      desc: t('howFeatureMultiAgentDesc') || '4 specialized AI agents work together',
    },
    {
      icon: '📱',
      title: t('howFeaturePWA') || 'Installable PWA',
      desc: t('howFeaturePWADesc') || 'Works offline, installs on any device',
    },
    {
      icon: '📚',
      title: t('howFeatureHistory') || 'Chat History',
      desc: t('howFeatureHistoryDesc') || 'Save, reload, and rename any past session',
    },
  ]

  const colors = {
    blue: 'bg-blue-100 text-blue-600 border-blue-300',
    purple: 'bg-purple-100 text-purple-600 border-purple-300',
    green: 'bg-green-100 text-green-600 border-green-300',
    yellow: 'bg-yellow-100 text-yellow-600 border-yellow-300',
    indigo: 'bg-indigo-100 text-indigo-600 border-indigo-300',
    red: 'bg-red-100 text-red-600 border-red-300',
    pink: 'bg-pink-100 text-pink-600 border-pink-300',
  }

  const toolAccents = {
    blue: {
      ring: 'border-blue-300 bg-blue-50/60',
      badge: 'bg-blue-500 text-white',
      dot: 'bg-blue-500',
      stepBorder: 'border-blue-200',
    },
    green: {
      ring: 'border-green-300 bg-green-50/60',
      badge: 'bg-green-500 text-white',
      dot: 'bg-green-500',
      stepBorder: 'border-green-200',
    },
    purple: {
      ring: 'border-purple-300 bg-purple-50/60',
      badge: 'bg-purple-500 text-white',
      dot: 'bg-purple-500',
      stepBorder: 'border-purple-200',
    },
  }

  const currentTool = tools[activeTool]

  return (
    <div className="p-3 sm:p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-6 sm:mb-10">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-3">
          🎯 {t('howPageTitle') || 'How ReviewMind Works'}
        </h1>
        <p className="text-sm sm:text-base text-gray-600 max-w-3xl mx-auto">
          {t('howPageSubtitle') ||
            'ReviewMind automates the entire systematic literature review workflow — from paper search to final report — using 4 specialized AI agents. Here is the full pipeline in 7 simple steps.'}
        </p>
      </div>

      {/* SECTION 1 — Core Review Pipeline */}
      <div className="mb-4">
        <h2 className="text-sm sm:text-lg font-bold text-gray-500 uppercase tracking-wider text-center mb-4">
          🔬 Part 1 — Core Review Pipeline
        </h2>
      </div>

      {/* Pipeline Overview — wraps on mobile */}
      <div className="mb-6 sm:mb-10">
        <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2">
          {steps.map((step, idx) => (
            <React.Fragment key={step.id}>
              <button
                onClick={() => setActiveStep(idx)}
                className={`flex flex-col items-center p-2 sm:p-3 rounded-xl border-2 transition min-w-[60px] sm:min-w-[80px] ${
                  activeStep === idx
                    ? colors[step.color] + ' scale-105 sm:scale-110 shadow-md'
                    : 'bg-white border-gray-200 hover:border-gray-400'
                }`}
              >
                <span className="text-xl sm:text-2xl mb-1">{step.icon}</span>
                <span className="text-[9px] sm:text-[10px] font-semibold text-center leading-tight">
                  {step.short}
                </span>
              </button>
              {idx < steps.length - 1 && (
                <span className="text-gray-400 text-base sm:text-xl">→</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Active Step Detail Card */}
      <div
        className={`mb-8 sm:mb-12 p-4 sm:p-6 rounded-2xl border-2 ${colors[steps[activeStep].color]} bg-opacity-40`}
      >
        <div className="flex flex-col sm:flex-row items-start gap-3 sm:gap-4">
          <span className="text-4xl sm:text-5xl">{steps[activeStep].icon}</span>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-white border">
                {t('howStepLabel') || 'Step'} {steps[activeStep].id}
              </span>
              <h2 className="text-lg sm:text-2xl font-bold text-gray-800">
                {steps[activeStep].title}
              </h2>
            </div>
            <p className="text-sm sm:text-base text-gray-700 leading-relaxed mb-3">
              {steps[activeStep].description}
            </p>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="font-semibold text-gray-600">
                🛠️ {t('howTechUsed') || 'Tech used'}:
              </span>
              <span className="px-2 py-0.5 bg-white border rounded-full text-gray-700">
                {steps[activeStep].tech}
              </span>
            </div>
          </div>
        </div>

        {/* Nav buttons */}
        <div className="flex justify-between mt-6">
          <button
            onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
            disabled={activeStep === 0}
            className="px-3 sm:px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 disabled:opacity-30"
          >
            ← {t('howPrev') || 'Previous'}
          </button>
          <button
            onClick={() =>
              setActiveStep(Math.min(steps.length - 1, activeStep + 1))
            }
            disabled={activeStep === steps.length - 1}
            className="px-3 sm:px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 disabled:opacity-30"
          >
            {t('howNext') || 'Next'} →
          </button>
        </div>
      </div>

      {/* SECTION 2 — Companion Tools */}
      <div className="mb-6">
        <h2 className="text-sm sm:text-lg font-bold text-gray-500 uppercase tracking-wider text-center mb-2">
          🧰 Part 2 — Companion Tools
        </h2>
        <p className="text-center text-xs sm:text-sm text-gray-600 max-w-2xl mx-auto mb-6">
          Beyond the review pipeline, ReviewMind includes three powerful tools
          that work on any content — not just research papers.
        </p>
      </div>

      {/* Tool Selector Tabs */}
      <div className="flex flex-wrap justify-center gap-2 sm:gap-3 mb-6">
        {tools.map((tool, idx) => {
          const a = toolAccents[tool.accent]
          const isActive = activeTool === idx
          return (
            <button
              key={tool.key}
              onClick={() => setActiveTool(idx)}
              className={`flex items-center gap-2 px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl border-2 text-xs sm:text-sm font-semibold transition ${
                isActive
                  ? a.ring + ' shadow-md scale-105'
                  : 'bg-white border-gray-200 text-gray-600 hover:border-gray-400'
              }`}
            >
              <span className="text-base sm:text-lg">{tool.icon}</span>
              {tool.name}
            </button>
          )
        })}
      </div>

      {/* Active Tool Detail */}
      <div
        className={`mb-8 sm:mb-12 rounded-2xl border-2 ${toolAccents[currentTool.accent].ring} p-4 sm:p-6`}
      >
        <div className="flex items-center gap-3 mb-1">
          <span className="text-3xl sm:text-4xl">{currentTool.icon}</span>
          <div>
            <h3 className="text-base sm:text-xl font-bold text-gray-800">
              {currentTool.name}
            </h3>
            <p className="text-xs sm:text-sm text-gray-600">
              {currentTool.tagline}
            </p>
          </div>
        </div>

        {/* Sub-steps — stack on mobile */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 sm:gap-3 mt-5">
          {currentTool.steps.map((s, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-2 sm:gap-3 p-2 sm:p-3 rounded-xl bg-white border ${toolAccents[currentTool.accent].stepBorder}`}
            >
              <div
                className={`flex-shrink-0 w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-xs font-bold ${toolAccents[currentTool.accent].badge}`}
              >
                {idx + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-sm sm:text-base">{s.icon}</span>
                  <h4 className="text-xs sm:text-sm font-bold text-gray-800">
                    {s.title}
                  </h4>
                </div>
                <p className="text-[11px] sm:text-xs text-gray-600 leading-relaxed">
                  {s.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* CTA for the active tool */}
        <div className="mt-5 text-center">
          <button
            onClick={() => {
              if (currentTool.key === 'chat') navigate('/chat')
              if (currentTool.key === 'quiz') navigate('/quiz')
              if (currentTool.key === 'presentation') navigate('/presentation')
            }}
            className="px-4 sm:px-5 py-2 text-xs sm:text-sm font-medium text-white rounded-lg shadow-sm hover:shadow-md transition"
            style={{
              backgroundColor:
                currentTool.accent === 'blue'
                  ? '#2563eb'
                  : currentTool.accent === 'green'
                  ? '#16a34a'
                  : '#9333ea',
            }}
          >
            Try {currentTool.name} →
          </button>
        </div>
      </div>

      {/* SECTION 3 — Key Features Grid */}
      <div className="mb-8 sm:mb-12">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-6 text-center">
          ⭐ {t('howKeyFeatures') || 'Key Features'}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          {features.map((f, idx) => (
            <div
              key={idx}
              className="bg-white border border-gray-200 rounded-xl p-3 sm:p-5 hover:shadow-lg transition"
            >
              <div className="text-2xl sm:text-3xl mb-2">{f.icon}</div>
              <h3 className="text-sm sm:text-base font-bold text-gray-800 mb-1">
                {f.title}
              </h3>
              <p className="text-xs sm:text-sm text-gray-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className="mb-8 sm:mb-12 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-2xl p-4 sm:p-6">
        <h2 className="text-lg sm:text-xl font-bold text-gray-800 mb-4 text-center">
          🛠️ {t('howTechStack') || 'Technology Stack'}
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 text-center">
          <div>
            <p className="text-[10px] sm:text-xs font-semibold text-gray-500 uppercase mb-1">
              Frontend
            </p>
            <p className="text-xs sm:text-sm text-gray-800">
              React • Vite • Tailwind
            </p>
          </div>
          <div>
            <p className="text-[10px] sm:text-xs font-semibold text-gray-500 uppercase mb-1">
              Backend
            </p>
            <p className="text-xs sm:text-sm text-gray-800">
              FastAPI • Python 3.12
            </p>
          </div>
          <div>
            <p className="text-[10px] sm:text-xs font-semibold text-gray-500 uppercase mb-1">
              AI / ML
            </p>
            <p className="text-xs sm:text-sm text-gray-800">
              Gemini 2.5 • scikit-learn
            </p>
          </div>
          <div>
            <p className="text-[10px] sm:text-xs font-semibold text-gray-500 uppercase mb-1">
              Data Sources
            </p>
            <p className="text-xs sm:text-sm text-gray-800">
              Semantic Scholar • OpenAlex
            </p>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="text-center py-6 sm:py-8 bg-white border-2 border-dashed border-blue-300 rounded-2xl">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-2">
          🚀 {t('howCtaTitle') || 'Ready to try it?'}
        </h2>
        <p className="text-sm sm:text-base text-gray-600 mb-4">
          {t('howCtaDesc') ||
            'Start your first systematic literature review in few minutes.'}
        </p>
        <button
          onClick={() => navigate('/review')}
          className="px-6 sm:px-8 py-2.5 sm:py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-medium shadow-md text-sm sm:text-base"
        >
          {t('howCtaButton') || 'Start Literature Review'} →
        </button>
      </div>
    </div>
  )
}

export default HowItWorks
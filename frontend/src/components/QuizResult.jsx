import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

/**
 * QuizResult — Compact, theme-consistent result page.
 * Blue-primary design matching the rest of the site.
 * Props: questions, answers, score, onRestart, onViewHistory (optional)
 */
function QuizResult({ questions, answers, score, onRestart, onViewHistory }) {
  const { t } = useTranslation()
  const [showConfetti, setShowConfetti] = useState(false)
  const [animatedScore, setAnimatedScore] = useState(0)
  const [showReview, setShowReview] = useState(false)

  const totalQuestions = score?.total ?? questions.length
  const correctCount = score?.correct ?? 0
  const wrongCount = totalQuestions - correctCount
  const percentage = score?.percentage ?? 0

  // Celebration config — theme-consistent colors (compact)
  const getCelebration = () => {
    if (percentage >= 90) {
      return {
        emoji: '🏆',
        title: 'LEGENDARY!',
        badge: '🥇 GOLD TIER',
        badgeClass: 'bg-gradient-to-r from-amber-500 to-yellow-500 text-white',
        accentColor: 'text-amber-600',
        accentBg: 'from-amber-500 to-yellow-500',
        borderClass: 'border-amber-300',
        bgClass: 'bg-gradient-to-br from-amber-50 to-white',
        confetti: true,
      }
    }
    if (percentage >= 75) {
      return {
        emoji: '🎉',
        title: 'EXCELLENT!',
        badge: '🥈 SILVER TIER',
        badgeClass: 'bg-gradient-to-r from-slate-400 to-slate-500 text-white',
        accentColor: 'text-emerald-600',
        accentBg: 'from-emerald-500 to-teal-500',
        borderClass: 'border-emerald-300',
        bgClass: 'bg-gradient-to-br from-emerald-50 to-white',
        confetti: true,
      }
    }
    if (percentage >= 60) {
      return {
        emoji: '👍',
        title: 'GOOD JOB!',
        badge: '🥉 BRONZE TIER',
        badgeClass: 'bg-gradient-to-r from-orange-400 to-orange-500 text-white',
        accentColor: 'text-blue-600',
        accentBg: 'from-blue-500 to-cyan-500',
        borderClass: 'border-blue-300',
        bgClass: 'bg-gradient-to-br from-blue-50 to-white',
        confetti: false,
      }
    }
    if (percentage >= 40) {
      return {
        emoji: '📖',
        title: 'KEEP GOING!',
        badge: '💪 RISING STAR',
        badgeClass: 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white',
        accentColor: 'text-blue-600',
        accentBg: 'from-blue-500 to-indigo-500',
        borderClass: 'border-blue-300',
        bgClass: 'bg-gradient-to-br from-blue-50 to-white',
        confetti: false,
      }
    }
    return {
      emoji: '💪',
      title: "DON'T GIVE UP!",
      badge: '🌱 NEW BEGINNER',
      badgeClass: 'bg-gradient-to-r from-slate-500 to-gray-600 text-white',
      accentColor: 'text-indigo-600',
      accentBg: 'from-indigo-500 to-purple-500',
      borderClass: 'border-indigo-300',
      bgClass: 'bg-gradient-to-br from-indigo-50 to-white',
      confetti: false,
    }
  }

  const celebration = getCelebration()

  // Confetti animation (only for high scores)
  useEffect(() => {
    if (celebration.confetti) {
      setShowConfetti(true)
      const timer = setTimeout(() => setShowConfetti(false), 5000)
      return () => clearTimeout(timer)
    }
  }, [celebration.confetti])

  // Animate score number 0 → percentage
  useEffect(() => {
    let current = 0
    const increment = percentage / 50
    const timer = setInterval(() => {
      current += increment
      if (current >= percentage) {
        setAnimatedScore(percentage)
        clearInterval(timer)
      } else {
        setAnimatedScore(Math.floor(current))
      }
    }, 20)
    return () => clearInterval(timer)
  }, [percentage])

  // Confetti Component
  const Confetti = () => {
    const pieces = Array.from({ length: 40 })
    return (
      <div className="fixed inset-0 pointer-events-none z-40 overflow-hidden">
        {pieces.map((_, i) => {
          const left = Math.random() * 100
          const delay = Math.random() * 3
          const duration = 3 + Math.random() * 2
          const emoji = ['🎉', '🎊', '⭐', '✨', '🌟'][Math.floor(Math.random() * 5)]
          return (
            <div
              key={i}
              className="absolute text-2xl animate-confetti"
              style={{
                left: `${left}%`,
                top: '-50px',
                animationDelay: `${delay}s`,
                animationDuration: `${duration}s`,
              }}
            >
              {emoji}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Confetti */}
      {showConfetti && <Confetti />}

      {/* MAIN SCORE CARD — compact */}
      <div className={`rounded-2xl border-2 ${celebration.borderClass} ${celebration.bgClass} shadow-md overflow-hidden`}>
        {/* Top Decorative Bar */}
        <div className={`h-1.5 bg-gradient-to-r ${celebration.accentBg}`} />

        <div className="p-5 text-center">
          {/* Emoji — smaller, no bounce */}
          <div className="text-4xl mb-2">{celebration.emoji}</div>

          {/* Badge */}
          <div className={`inline-block px-3 py-1 rounded-full ${celebration.badgeClass} text-[10px] font-bold mb-2 tracking-wider shadow-sm`}>
            {celebration.badge}
          </div>

          {/* Title */}
          <h1 className={`text-2xl md:text-3xl font-black ${celebration.accentColor} mb-1`}>
            {celebration.title}
          </h1>

          {/* SCORE CIRCLE — smaller */}
          <div className="flex justify-center my-4">
            <div className="relative">
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="54"
                  stroke="#e5e7eb"
                  strokeWidth="8"
                  fill="none"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="54"
                  stroke="url(#scoreGradient)"
                  strokeWidth="8"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 54}`}
                  strokeDashoffset={`${2 * Math.PI * 54 * (1 - animatedScore / 100)}`}
                  className="transition-all duration-1000 ease-out"
                />
                <defs>
                  <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="text-3xl font-black text-blue-600">
                  {animatedScore}%
                </div>
                <div className="text-[10px] text-gray-500 font-bold tracking-wider">
                  SCORE
                </div>
              </div>
            </div>
          </div>

          {/* STATS ROW — compact */}
          <div className="grid grid-cols-3 gap-2 max-w-sm mx-auto mb-4">
            <div className="bg-green-50 border border-green-200 rounded-lg py-2">
              <div className="text-xl font-bold text-green-600">{correctCount}</div>
              <div className="text-[10px] text-green-700 font-medium mt-0.5">
                ✅ Correct
              </div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg py-2">
              <div className="text-xl font-bold text-red-600">{wrongCount}</div>
              <div className="text-[10px] text-red-700 font-medium mt-0.5">
                ❌ Wrong
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg py-2">
              <div className="text-xl font-bold text-blue-600">{totalQuestions}</div>
              <div className="text-[10px] text-blue-700 font-medium mt-0.5">
                📊 Total
              </div>
            </div>
          </div>

          {/* ACTION BUTTONS — 2 main + 1 history */}
          <div className="flex flex-wrap gap-2 justify-center mb-2">
            <button
              onClick={onRestart}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold shadow-sm hover:shadow-md transition-all text-sm"
            >
              🎯 Start New Quiz
            </button>
            <button
              onClick={() => setShowReview(!showReview)}
              className="px-5 py-2 bg-white border-2 border-blue-300 text-blue-700 rounded-lg font-semibold shadow-sm hover:border-blue-500 hover:bg-blue-50 transition-all text-sm"
            >
              {showReview ? '📕 Hide Answers' : '📖 Review Answers'}
            </button>
          </div>

          {/* View History button — inside card */}
          {onViewHistory && (
            <button
              onClick={onViewHistory}
              className="text-xs text-blue-600 hover:text-blue-800 hover:underline font-medium mt-2"
            >
              📚 View Quiz History
            </button>
          )}
        </div>
      </div>

      {/* REVIEW SECTION (collapsible) */}
      {showReview && (
        <div className="mt-4 animate-fadeIn">
          <h3 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
            📋 Answer Review
            <span className="text-xs font-normal text-gray-500">
              ({correctCount}/{totalQuestions} correct)
            </span>
          </h3>

          <div className="space-y-2">
            {questions.map((q, idx) => {
              const userAns = answers[idx]
              const isCorrect = userAns === q.correct_index
              return (
                <div
                  key={idx}
                  className={`p-3 border-2 rounded-xl ${
                    isCorrect
                      ? 'border-green-300 bg-green-50'
                      : 'border-red-300 bg-red-50'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <div
                      className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                        isCorrect ? 'bg-green-500' : 'bg-red-500'
                      }`}
                    >
                      {isCorrect ? '✓' : '✗'}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-bold text-gray-800 mb-1.5">
                        Q{idx + 1}. {q.question}
                      </p>
                      <div className="space-y-1">
                        <p className="text-xs">
                          <span className="font-semibold text-gray-600">
                            Your answer:{' '}
                          </span>
                          <span
                            className={
                              isCorrect ? 'text-green-700' : 'text-red-700'
                            }
                          >
                            {userAns !== null && userAns !== undefined
                              ? q.options[userAns]
                              : '❓ Not answered'}
                          </span>
                        </p>
                        {!isCorrect && (
                          <p className="text-xs">
                            <span className="font-semibold text-gray-600">
                              Correct answer:{' '}
                            </span>
                            <span className="text-green-700">
                              {q.options[q.correct_index]}
                            </span>
                          </p>
                        )}
                        {q.explanation && (
                          <div className="mt-1.5 p-2 bg-white border border-blue-200 rounded-lg">
                            <p className="text-xs text-blue-800">
                              💡 <strong>Explanation:</strong> {q.explanation}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default QuizResult
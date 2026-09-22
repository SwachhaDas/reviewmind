import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE } from '../api'

function QuizGenerator({ contextText }) {
  const { t, i18n } = useTranslation()
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    if (!contextText) return
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/quiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context_text: contextText, num_questions: 5, lang: i18n.language }),
      })
      const data = await res.json()
      setQuestions(data.questions || [])
    } catch (err) {
      setQuestions([])
    }
    setLoading(false)
  }

  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="font-semibold text-sm">{t('quizTitle')}</p>
        <button
          onClick={generate}
          disabled={loading}
          className="px-4 py-1.5 bg-purple-500 text-white rounded-lg text-sm disabled:opacity-50"
        >
          {loading ? '...' : t('generateQuiz')}
        </button>
      </div>
      <div className="space-y-3">
        {questions.map((q, i) => (
          <div key={i} className="text-sm border-t pt-2">
            <p className="font-medium mb-1">{i + 1}. {q.question}</p>
            <ul className="space-y-1">
              {q.options?.map((opt, oi) => (
                <li
                  key={oi}
                  className={`px-2 py-1 rounded ${oi === q.correct_index ? 'bg-green-100' : 'bg-gray-50'}`}
                >
                  {opt}
                </li>
              ))}
            </ul>
            {q.explanation && <p className="text-xs text-gray-500 mt-1">{q.explanation}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}

export default QuizGenerator

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE } from '../api'

function PaperChat({ contextText }) {
  const { t, i18n } = useTranslation()
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const ask = async () => {
    if (!question.trim() || !contextText) return
    const q = question
    setMessages((m) => [...m, { role: 'user', text: q }])
    setQuestion('')
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context_text: contextText, question: q, lang: i18n.language }),
      })
      const data = await res.json()
      setMessages((m) => [...m, { role: 'ai', text: data.answer }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'ai', text: 'Error: ' + err.message }])
    }
    setLoading(false)
  }

  return (
    <div className="bg-white border rounded-lg p-4">
      <p className="font-semibold text-sm mb-2">{t('chatTitle')}</p>
      <div className="space-y-2 max-h-48 overflow-y-auto mb-2">
        {messages.map((m, i) => (
          <div key={i} className={`text-sm p-2 rounded-lg ${m.role === 'user' ? 'bg-blue-50 ml-8' : 'bg-gray-100 mr-8'}`}>
            {m.text}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask()}
          placeholder={t('chatPlaceholder')}
          className="flex-1 px-3 py-1.5 border rounded-lg text-sm"
        />
        <button
          onClick={ask}
          disabled={loading}
          className="px-4 py-1.5 bg-blue-500 text-white rounded-lg text-sm disabled:opacity-50"
        >
          {t('send')}
        </button>
      </div>
    </div>
  )
}

export default PaperChat

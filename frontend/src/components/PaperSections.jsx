import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'

/**
 * Reusable collapsible section component.
 */
function Section({ title, icon, text, color = 'blue' }) {
  const [expanded, setExpanded] = useState(false)

  if (!text || !text.trim()) return null

  const preview = text.slice(0, 400)
  const isLong = text.length > 400

  return (
    <div className="border rounded-lg overflow-hidden mb-3">
      <div
        className={`flex items-center justify-between px-4 py-2 bg-${color}-50 border-b`}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <span className={`font-semibold text-${color}-800 text-sm uppercase tracking-wide`}>
            {title}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {text.length.toLocaleString()} chars
        </span>
      </div>

      <div className="px-4 py-3 bg-white">
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
          {expanded ? text : preview}
          {!expanded && isLong && '…'}
        </p>

        {isLong && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 text-xs text-blue-600 hover:text-blue-800 font-medium"
          >
            {expanded ? '▲ Show less' : '▼ Show more'}
          </button>
        )}
      </div>
    </div>
  )
}

/**
 * Get display label for content type.
 */
function contentTypeLabel(type) {
  const labels = {
    research_paper: '📄 Research Paper',
    wikipedia: '📚 Wikipedia',
    blog: '📰 Blog',
    code: '💻 Code',
    notes: '📓 Notes',
    other: '📄 Document',
    unknown: '📄 Document',
  }
  return labels[type] || '📄 Document'
}

function PaperSections({ paper }) {
  const { t } = useTranslation()

  if (!paper) return null

  const isResearchPaper = paper.content_type === 'research_paper'
  const isOtherContent = !isResearchPaper

  const researchSections = [
    { key: 'abstract', icon: '📝', color: 'blue', title: 'Abstract' },
    { key: 'introduction', icon: '📖', color: 'purple', title: 'Introduction' },
    { key: 'methodology', icon: '🔬', color: 'green', title: 'Methodology' },
    { key: 'findings', icon: '📊', color: 'yellow', title: 'Findings' },
    { key: 'limitations', icon: '⚠️', color: 'red', title: 'Limitations' },
    { key: 'conclusion', icon: '🎯', color: 'indigo', title: 'Conclusion' },
  ]

  const hasAnySection = researchSections.some((s) => paper[s.key])

  return (
    <div>
      {/* Paper header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 mb-4">
        <h2 className="text-lg font-bold text-gray-800 mb-2 leading-snug">
          📄 {paper.title || 'Untitled'}
        </h2>

        <div className="flex flex-wrap gap-2 text-xs text-gray-600">
          {paper.char_count > 0 && (
            <span>📏 {paper.char_count.toLocaleString()} {t('charsLabel')}</span>
          )}
          {paper.word_count > 0 && (
            <span>📝 {paper.word_count.toLocaleString()} {t('wordsLabel')}</span>
          )}

          {/* Content type badge */}
          {paper.content_type && (
            <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full font-medium">
              {contentTypeLabel(paper.content_type)}
            </span>
          )}

          {/* Source badge */}
          {paper.source === 'pasted' && (
            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">
              📝 {t('sourcePastedText')}
            </span>
          )}
          {paper.source === 'uploaded' && (
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full font-medium">
              📎 {t('sourcePDFUpload')}
            </span>
          )}
        </div>
      </div>

      {/* Content rendering */}
      <div className="max-h-[600px] overflow-y-auto pr-1">
        {isResearchPaper ? (
          // ─── Research paper: 6 sections ───
          hasAnySection ? (
            researchSections.map((s) => (
              <Section
                key={s.key}
                title={s.title}
                icon={s.icon}
                color={s.color}
                text={paper[s.key] || ''}
              />
            ))
          ) : (
            <div className="text-center text-gray-500 py-8">
              <p className="text-4xl mb-2">📭</p>
              <p className="text-sm">{t('noSectionsDetected')}</p>
            </div>
          )
        ) : (
          // ─── Non-research content: Summary + Key Points + Full Text ───
          <>
            {/* Summary */}
            {paper.abstract && (
              <Section
                title="Summary"
                icon="📝"
                color="blue"
                text={paper.abstract}
              />
            )}

            {/* Key Points */}
            {paper.key_points && paper.key_points.length > 0 && (
              <div className="border rounded-lg overflow-hidden mb-3">
                <div className="flex items-center justify-between px-4 py-2 bg-yellow-50 border-b">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">⭐</span>
                    <span className="font-semibold text-yellow-800 text-sm uppercase tracking-wide">
                      Key Points
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {paper.key_points.length} items
                  </span>
                </div>
                <div className="px-4 py-3 bg-white">
                  <ul className="space-y-2">
                    {paper.key_points.map((point, i) => (
                      <li key={i} className="flex gap-2 text-sm text-gray-700 leading-relaxed">
                        <span className="text-yellow-600 font-bold flex-shrink-0">
                          {i + 1}.
                        </span>
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Full Content */}
            <Section
              title="Full Content"
              icon="📖"
              color="gray"
              text={paper.full_text || ''}
            />
          </>
        )}
      </div>
    </div>
  )
}

export default PaperSections
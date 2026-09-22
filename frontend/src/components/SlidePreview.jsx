import React, { useState } from 'react'

/**
 * SlidePreview — Displays slides one at a time with prev/next navigation.
 * Blue theme matching the rest of the website.
 *
 * Props:
 *   slides    (array)  — [{ title, bullets: [...] }, ...]
 *   title     (string) — optional presentation title (shown in footer)
 *   subtitle  (string) — optional subtitle (unused visually but kept for future)
 */
function SlidePreview({ slides, title, subtitle }) {
  const [index, setIndex] = useState(0)
  const total = slides?.length || 0

  // ── Empty state ──
  if (!slides || total === 0) {
    return (
      <div className="text-center text-sm text-gray-500 py-12">
        No slides to preview.
      </div>
    )
  }

  const slide = slides[index]
  const bullets = slide.bullets || []

  return (
    <div>
      {/* ── Top bar: counter + nav buttons ── */}
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-medium text-gray-600">
          Slide {index + 1} of {total}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIndex(Math.max(0, index - 1))}
            disabled={index === 0}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition"
          >
            ← Prev
          </button>
          <button
            onClick={() => setIndex(Math.min(total - 1, index + 1))}
            disabled={index === total - 1}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-blue-500 bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-40 transition"
          >
            Next →
          </button>
        </div>
      </div>

      {/* ── Slide canvas (16:9-ish aspect) ── */}
      <div className="w-full rounded-2xl border-2 border-blue-200 shadow-md overflow-hidden bg-white">
        {/* Top blue accent bar */}
        <div className="h-1.5 bg-gradient-to-r from-blue-500 to-indigo-500" />

        <div className="p-8 min-h-[320px]">
          {/* Slide title */}
          <h3 className="text-xl md:text-2xl font-bold text-blue-900 mb-1">
            {slide.title}
          </h3>
          {/* Accent underline */}
          <div className="w-16 h-0.5 bg-blue-500 rounded-full mb-5" />

          {/* Bullets */}
          <ul className="space-y-2.5">
            {bullets.length === 0 ? (
              <li className="text-sm text-gray-400 italic">
                (No content on this slide)
              </li>
            ) : (
              bullets.map((b, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-gray-800"
                >
                  <span className="text-blue-500 font-bold mt-0.5">•</span>
                  <span className="leading-relaxed">{b}</span>
                </li>
              ))
            )}
          </ul>
        </div>

        {/* Footer strip */}
        <div className="px-6 py-2 bg-blue-50 border-t border-blue-100 flex items-center justify-between">
          <span className="text-[10px] text-gray-500 font-medium truncate max-w-[60%]">
            {title || 'ReviewMind Presentation'}
          </span>
          <span className="text-[10px] text-gray-400">
            {index + 1} / {total}
          </span>
        </div>
      </div>

      {/* ── Dot indicators ── */}
      <div className="flex flex-wrap justify-center gap-1.5 mt-4">
        {slides.map((_, i) => (
          <button
            key={i}
            onClick={() => setIndex(i)}
            className={`h-2 rounded-full transition-all ${
              i === index
                ? 'bg-blue-600 w-6'
                : 'bg-gray-300 hover:bg-gray-400 w-2'
            }`}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  )
}

export default SlidePreview
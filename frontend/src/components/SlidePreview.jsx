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
      {/* ── Top bar: counter + nav buttons ──
          Mobile: counter on one line, buttons stretch below to keep
          tap targets comfortable on narrow screens. */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0 mb-3">
        <div className="text-xs sm:text-sm font-medium text-gray-600">
          Slide {index + 1} of {total}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIndex(Math.max(0, index - 1))}
            disabled={index === 0}
            className="flex-1 sm:flex-none px-3 py-2 sm:py-1.5 text-xs sm:text-xs font-medium rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition"
          >
            ← Prev
          </button>
          <button
            onClick={() => setIndex(Math.min(total - 1, index + 1))}
            disabled={index === total - 1}
            className="flex-1 sm:flex-none px-3 py-2 sm:py-1.5 text-xs sm:text-xs font-medium rounded-lg border border-blue-500 bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-40 transition"
          >
            Next →
          </button>
        </div>
      </div>

      {/* ── Slide canvas (16:9-ish aspect) ──
          Padding and min-height scale with viewport so mobile devices
          don't waste vertical space on oversized whitespace. */}
      <div className="w-full rounded-xl sm:rounded-2xl border-2 border-blue-200 shadow-md overflow-hidden bg-white">
        {/* Top blue accent bar */}
        <div className="h-1 sm:h-1.5 bg-gradient-to-r from-blue-500 to-indigo-500" />

        <div className="p-4 sm:p-6 md:p-8 min-h-[220px] sm:min-h-[280px] md:min-h-[320px]">
          {/* Slide title — break-words prevents long titles from
              overflowing the canvas on narrow screens. */}
          <h3 className="text-base sm:text-xl md:text-2xl font-bold text-blue-900 mb-1 break-words">
            {slide.title}
          </h3>
          {/* Accent underline */}
          <div className="w-12 sm:w-16 h-0.5 bg-blue-500 rounded-full mb-3 sm:mb-5" />

          {/* Bullets — text-base on mobile improves readability;
              leading-relaxed on the inner span keeps line spacing airy. */}
          <ul className="space-y-2 sm:space-y-2.5">
            {bullets.length === 0 ? (
              <li className="text-sm text-gray-400 italic">
                (No content on this slide)
              </li>
            ) : (
              bullets.map((b, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm sm:text-base text-gray-800"
                >
                  <span className="text-blue-500 font-bold mt-0.5 flex-shrink-0">
                    •
                  </span>
                  <span className="leading-relaxed break-words">{b}</span>
                </li>
              ))
            )}
          </ul>
        </div>

        {/* Footer strip — title clamps tighter on mobile so the
            page counter on the right stays visible. */}
        <div className="px-4 sm:px-6 py-2 bg-blue-50 border-t border-blue-100 flex items-center justify-between gap-2">
          <span className="text-[10px] text-gray-500 font-medium truncate max-w-[55%] sm:max-w-[60%]">
            {title || 'ReviewMind Presentation'}
          </span>
          <span className="text-[10px] text-gray-400 flex-shrink-0">
            {index + 1} / {total}
          </span>
        </div>
      </div>

      {/* ── Dot indicators ──
          Visual dot stays small, but the wrapping button gets extra
          padding on mobile so the tap target is comfortable (~32px)
          without enlarging the dot itself. */}
      <div className="flex flex-wrap justify-center gap-0.5 sm:gap-1.5 mt-3 sm:mt-4">
        {slides.map((_, i) => (
          <button
            key={i}
            onClick={() => setIndex(i)}
            className="p-1.5 sm:p-0 flex items-center justify-center"
            aria-label={`Go to slide ${i + 1}`}
          >
            <span
              className={`h-2 rounded-full transition-all block ${
                i === index
                  ? 'bg-blue-600 w-6'
                  : 'bg-gray-300 hover:bg-gray-400 w-2'
              }`}
            />
          </button>
        ))}
      </div>
    </div>
  )
}

export default SlidePreview
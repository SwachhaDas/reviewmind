import React from 'react'

/**
 * QuizCard — displays one MCQ question with 4 options.
 * Highlights correct/incorrect after selection.
 */
function QuizCard({ question, index, total, selectedIndex, onSelect }) {
  const isAnswered = selectedIndex !== null && selectedIndex !== undefined

  const getOptionStyle = (optIdx) => {
    if (!isAnswered) {
      return 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50 cursor-pointer'
    }
    if (optIdx === question.correct_index) {
      return 'border-green-500 bg-green-50 text-green-800 cursor-default'
    }
    if (optIdx === selectedIndex) {
      return 'border-red-500 bg-red-50 text-red-800 cursor-default'
    }
    return 'border-gray-200 bg-gray-50 text-gray-500 cursor-default'
  }

  const getLetter = (i) => String.fromCharCode(65 + i)

  return (
    <div className="bg-white border rounded-2xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-bold px-3 py-1 bg-blue-100 text-blue-700 rounded-full">
          Question {index + 1} / {total}
        </span>
        {isAnswered && (
          <span
            className={`text-xs font-bold px-3 py-1 rounded-full ${
              selectedIndex === question.correct_index
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {selectedIndex === question.correct_index ? '✅ Correct' : '❌ Incorrect'}
          </span>
        )}
      </div>

      {/* Question */}
      <h3 className="text-lg font-semibold text-gray-800 mb-5 leading-relaxed">
        {question.question}
      </h3>

      {/* Options */}
      <div className="space-y-3">
        {(question.options || []).map((option, optIdx) => (
          <button
            key={optIdx}
            onClick={() => !isAnswered && onSelect(optIdx)}
            disabled={isAnswered}
            className={`w-full text-left px-4 py-3 border-2 rounded-xl transition flex items-start gap-3 ${getOptionStyle(optIdx)}`}
          >
            <span
              className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ${
                isAnswered && optIdx === question.correct_index
                  ? 'bg-green-500 text-white'
                  : isAnswered && optIdx === selectedIndex
                  ? 'bg-red-500 text-white'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              {getLetter(optIdx)}
            </span>
            <span className="flex-1 text-sm leading-relaxed pt-1">{option}</span>
          </button>
        ))}
      </div>

      {/* Explanation */}
      {isAnswered && question.explanation && (
        <div className="mt-5 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <p className="text-xs font-bold text-blue-700 mb-1">💡 Explanation</p>
          <p className="text-sm text-gray-700 leading-relaxed">{question.explanation}</p>
        </div>
      )}
    </div>
  )
}

export default QuizCard
import React from 'react';

function ProgressTracker({ status }) {
  if (!status) return null;

  const {
    stage_label,
    progress_current,
    progress_total,
    elapsed,
    current_item,
    status: jobStatus,
    error,
  } = status;

  const percent =
    progress_total > 0
      ? Math.round((progress_current / progress_total) * 100)
      : 0;

  const formatTime = (s) => {
    if (!s) return '0s';
    if (s < 60) return `${Math.round(s)}s`;
    return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
  };

  const isComplete = jobStatus === 'complete';
  const isFailed = jobStatus === 'failed';

  return (
    <div
      className={`max-w-3xl mx-auto mt-6 p-4 rounded-lg border-2 ${
        isComplete
          ? 'bg-green-50 border-green-300'
          : isFailed
          ? 'bg-red-50 border-red-300'
          : 'bg-blue-50 border-blue-200'
      }`}
    >
      {/* Stage label + elapsed */}
      <div className="flex justify-between items-center mb-2">
        <span className="font-semibold text-gray-800">{stage_label}</span>
        <span className="text-sm text-gray-600">⏱️ {formatTime(elapsed)}</span>
      </div>

      {/* Progress bar */}
      {!isComplete && !isFailed && progress_total > 0 && (
        <>
          <div className="w-full bg-blue-200 rounded-full h-3 mb-2 overflow-hidden">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${percent}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-600 mb-2">
            <span>
              {progress_current} / {progress_total} ({percent}%)
            </span>
          </div>
        </>
      )}

      {/* Current paper */}
      {current_item && !isComplete && (
        <p className="text-sm text-gray-700 italic">📄 {current_item}</p>
      )}

      {/* Error */}
      {isFailed && (
        <p className="text-sm text-red-600 mt-2">❌ {error}</p>
      )}

      {/* Complete */}
      {isComplete && (
        <p className="text-sm text-green-700 font-medium">
          🎉 Finished in {formatTime(elapsed)}
        </p>
      )}
    </div>
  );
}

export default ProgressTracker;
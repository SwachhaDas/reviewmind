// ─────────────────────────────────────────────
// API base URL
// ─────────────────────────────────────────────
// Uses Vite environment variable if provided (production build), else
// falls back to localhost so local development works without any setup.
const _ENV_BASE = import.meta.env.VITE_API_BASE_URL
export const API_BASE = (_ENV_BASE && _ENV_BASE.trim()) || 'http://localhost:8000/api'

// Also export the server root (without /api) so components that build
// download URLs (e.g. presentation PPTX/PDF) can work consistently.
export const API_SERVER = API_BASE.replace(/\/api\/?$/, '')

// ─────────────────────────────────────────────
// Presentation API endpoints
// ─────────────────────────────────────────────
export const PRESENTATION_ENDPOINTS = {
  generate: `${API_BASE}/presentation/generate`,
  upload: `${API_BASE}/presentation/upload`,
  history: `${API_BASE}/presentation/history`,
  session: (id) => `${API_BASE}/presentation/history/${id}`,
  title: (id) => `${API_BASE}/presentation/history/${id}/title`,
  delete: (id) => `${API_BASE}/presentation/history/${id}`,
  download: (id, fmt) => `${API_BASE}/presentation/download/${id}/${fmt}`,
}

// ─────────────────────────────────────────────
// Review History API endpoints
// ─────────────────────────────────────────────
export const REVIEW_ENDPOINTS = {
  save: `${API_BASE}/review/history`,
  list: `${API_BASE}/review/history`,
  session: (id) => `${API_BASE}/review/history/${id}`,
  title: (id) => `${API_BASE}/review/history/${id}/title`,
  attachReport: (id) => `${API_BASE}/review/history/${id}/report`,
  delete: (id) => `${API_BASE}/review/history/${id}`,
}

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
// User ID — per-browser identity for history isolation
// ─────────────────────────────────────────────
import { getUserId } from './userId'

/**
 * Build headers object with X-User-Id attached.
 * Every history save/list/delete call MUST use this so the backend can
 * isolate sessions per browser (no cross-user visibility).
 */
export function userHeaders(extra = {}) {
  return {
    "X-User-Id": getUserId(),
    ...extra,
  }
}

/**
 * Convenience: userHeaders with JSON content-type.
 */
export function userJsonHeaders(extra = {}) {
  return userHeaders({
    "Content-Type": "application/json",
    ...extra,
  })
}

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
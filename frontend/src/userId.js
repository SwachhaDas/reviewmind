// userId.js — per-browser identity for history isolation.
// No login required; each browser gets a stable random UUID stored in
// localStorage. All history save/list calls attach this so one visitor
// never sees another visitor's sessions.

const STORAGE_KEY = "reviewmind_user_id";

function generateUUID() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // fallback for older browsers without crypto.randomUUID
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function getUserId() {
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = generateUUID();
    localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}
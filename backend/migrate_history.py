"""
migrate_history.py — One-time migration for old history files.

Old files may have two formats:
  1. { "sessions": [...] }  — wrapper format
  2. [ ... ]                — direct list format

Old sessions have no `user_id`. This script adds `user_id = "legacy"` to
every existing session so they don't disappear. To view them, a browser
would need X-User-Id: legacy — otherwise they stay hidden (fine for demo).

Run once:
    cd backend
    python migrate_history.py
"""
import json
import uuid
from pathlib import Path


DATA_DIR = Path(__file__).parent / "app" / "data"

FILES = [
    "review_history.json",
    "chat_history.json",
    "quiz_history.json",
    "presentation_history.json",
]

LEGACY_USER_ID = "legacy"


def migrate_file(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        print(f"[skip] {filename} not found")
        return

    try:
        # ⚠️ IMPORTANT: encoding='utf-8' — otherwise Windows cp1252 fails
        # on files containing emoji, Bengali, or any non-ASCII character.
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"[skip] {filename} — invalid JSON")
        return
    except UnicodeDecodeError as e:
        print(f"[skip] {filename} — decode error: {e}")
        return

    # Normalise to list
    if isinstance(raw, dict):
        sessions = raw.get("sessions", [])
    elif isinstance(raw, list):
        sessions = raw
    else:
        print(f"[skip] {filename} — unknown format")
        return

    changed = 0
    for s in sessions:
        if not isinstance(s, dict):
            continue
        if not s.get("user_id"):
            s["user_id"] = LEGACY_USER_ID
            changed += 1
        if not s.get("session_id"):
            s["session_id"] = str(uuid.uuid4())
        if not s.get("created_at"):
            s["created_at"] = s.get("updated_at") or 0

    # Save back as plain list — UTF-8 encoding
    path.write_text(
        json.dumps(sessions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] {filename}: {len(sessions)} sessions, "
          f"{changed} migrated to user_id='{LEGACY_USER_ID}'")


if __name__ == "__main__":
    print(f"Migrating files in {DATA_DIR}")
    for f in FILES:
        migrate_file(f)
    print("Done.")
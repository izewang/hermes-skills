# WebUI Sidebar Index (`_index.json`)

The sidebar in the Hermes WebUI is driven by `/home/hermeswebui/.hermes/webui/sessions/_index.json`.

## Structure

A JSON array of session objects. Each entry includes:

| Field | Description |
|-------|-------------|
| `session_id` | Session ID — **independent** mapping key, not automatically synced to state.db |
| `title` | Display name shown in the sidebar |
| `workspace` | Associated workspace path |
| `model` / `model_provider` | Model used |
| `message_count` | Message count (stale cached value) |
| `created_at` / `updated_at` / `last_message_at` | Timestamps |
| `pinned` / `archived` | Display state flags |
| `profile` | Hermes profile |
| `input_tokens` / `output_tokens` | Token counts |
| `cache_read_tokens` / `cache_hit_percent` | Cache stats |
| `pending_user_message` / `has_pending_user_message` | Draft state |
| `is_cli_session` | true for WeChat/WeCom sessions, false for WebUI-native sessions |
| `source_tag` / `source_label` | Origin (weixin, wecom, or null for WebUI) |
| `composer_draft` | Unsent draft content |

## Key Architectural Detail

The `session_id` in `_index.json` is an **independent pointer** into `state.db` — it is NOT automatically tied to the session that originally created that sidebar entry. This means:

- The sidebar can display a session under one title but load **different session data** from state.db
- Modifying the `session_id` in `_index.json` changes which state.db session the sidebar entry opens, without altering the title or any other metadata
- The `_index.json` only contains a **subset** of all sessions in state.db (e.g., 5 out of 11). CLI-only sessions (WeChat/WeCom) are only included if the WebUI session picks them up

## Relationship to state.db

- **state.db** (`sessions` table): the authoritative list of ALL sessions (11 in a typical setup)
- **_index.json**: a display index — only sessions visible in the sidebar are listed here
- **Session tree** (`session-tree.py`): reads from state.db, shows all sessions with branch structure

## Common Operations

### Redirect a sidebar entry to a different session

Find the target session_id from state.db, then edit `_index.json`:
```json
{
    "session_id": "<target-session-id-from-state-db>",
    "title": "Existing Display Title",
    ...
}
```

This is useful for debugging or re-linking sidebar entries to the correct session data.

### Finding a session_id by title from state.db

```python
import sqlite3, os
dh = os.environ.get("HERMES_HOME") or os.path.expanduser("~/.hermes")
conn = sqlite3.connect(os.path.join(dh, "state.db"))
cur = conn.cursor()
cur.execute("SELECT id, title FROM sessions WHERE title LIKE '%keyword%'")
# or list all:
cur.execute("SELECT id, title FROM sessions ORDER BY started_at")
rows = cur.fetchall()
conn.close()
```

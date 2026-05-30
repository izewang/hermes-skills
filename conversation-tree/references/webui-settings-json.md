# WebUI `settings.json`

The Hermes Dashboard WebUI stores its user-facing configuration in `~/.hermes/webui/settings.json`. This file controls what sessions and elements appear in the sidebar, plus display and behavior preferences.

## Session Visibility Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `show_cli_sessions` | bool | `true` | Show CLI-created sessions in the sidebar. Set `false` to hide them. |
| `show_previous_messaging_sessions` | bool | `false` | Show sessions from other messaging platforms (Telegram, WeCom, etc.) in the sidebar. |

## When a User Asks About CLI Session Display

The user may say **"把cli session的开关关了"** — this refers to `show_cli_sessions` in `settings.json`, **not** the Hermes agent config (`session_reset`, `group_sessions_per_user`, etc.). Do NOT start guessing agent-level config options; go directly to the WebUI settings file:

```bash
# Check current value
cat ~/.hermes/webui/settings.json | grep show_cli_sessions

# Toggle via patch or write_file
# Change "show_cli_sessions": true → "show_cli_sessions": false
```

## Other Notable Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sidebar_density` | string | `"compact"` | Sidebar item spacing: `"compact"` or `"comfortable"` |
| `session_jump_buttons` | bool | `false` | Show jump-to-top/bottom buttons in session list |
| `session_endless_scroll` | bool | `true` | Infinite scroll vs paginated session list |
| `pinned_sessions_limit` | number | `3` | Max pinned sessions shown |
| `theme` | string | `"light"` | UI theme (`"light"`, `"dark"`, `"system"`) |
| `skin` | string | `"geist-contrast"` | CSS skin variant |
| `hide_empty_state_suggestions` | bool | `false` | Suppress empty-state suggestions |
| `hidden_tabs` | array | `[]` | Tabs hidden from the sidebar |
| `onboarding_completed` | bool | `true` | Whether onboarding wizard has been shown |

## Location

```
~/.hermes/webui/settings.json
```

## Relationship to Sidebar Sessions

- The sidebar UI reads `settings.json` to decide **which sessions to show** (CLI vs messaging).
- The sidebar index (`_index.json` at `~/.hermes/webui/sessions/_index.json`) determines **which sessions exist** as sidebar entries.
- State.db (`~/.hermes/state.db`) has the **full list of ALL sessions** regardless of what's visible in the sidebar.

Changing `show_cli_sessions` does not delete sessions or affect state.db — it only toggles the sidebar filter. A page refresh is needed to see the change take effect.

## Common Pitfalls

- **Don't confuse with `session_reset.mode` in config.yaml.** `session_reset` controls auto-creating new sessions on idle/time; `show_cli_sessions` controls sidebar visibility only.
- **No restart needed** — just refresh the WebUI browser tab. Unlike Hermes agent config, `settings.json` is read live by the WebUI frontend.
- **The file is JSON, not YAML.** Use `write_file` or `patch` with JSON formatting, not YAML tools.

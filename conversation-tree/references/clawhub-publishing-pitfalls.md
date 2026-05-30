# ClawHub Publishing Pitfalls

## Summary

ClawHub (clawhub.ai) is OpenClaw's skill marketplace — not Hermes'. The CLI `--to clawhub` is a stub. Publishing via web UI is possible but has severe MCP-level limitations.

## Web UI Upload Flow

The publish page at `/skills/publish` requires:
- Actual OS folder drag-drop (webkitdirectory input)
- The folder must contain SKILL.md + scripts/ + references/
- Fill: Display Name, Slug, Icon (GitBranch recommended for tree tools)
- Check MIT-0 checkbox
- Click Publish

## Attempted Workarounds (all failed)

### 1. JavaScript DataTransfer
- Removed webkitdirectory attribute, uploaded SKILL.md via File constructor
- Page detected the file ("Skill folder selected, 1 file") BUT:
- Missing scripts/ and references/ caused "GitHub account lookup failed" on publish
- webkitRelativePath is read-only on File objects created via DataTransfer

### 2. Chrome DevTools MCP upload_file
- Targets file input element or its button wrapper
- Succeeds silently but page does NOT register the file
- Cannot upload multiple files to a webkitdirectory input

### 3. REST API (POST /api/v1/skills)
- Requires `Authorization: Bearer clh_...` (API token, not JWT)
- Multipart with payload JSON + files array
- Blocked by "MIT-0 license terms must be accepted" — undocumented parameter name
- Tried: acceptLicense, licenseAccepted, mit0_accepted, mit0, acceptTerms — all rejected
- Accepting MIT-0 via web UI checkbox does NOT persist to API token scope

### 4. Convex mutation (skills:publish)
- POST to deployment URL with JWT auth
- Returns empty response — parameter format unknown
- Probably expects file uploads not just JSON args

## Conclusion

For MCP-based browser automation, ClawHub publishing is effectively impossible. Requires manual drag-drop by a human user.

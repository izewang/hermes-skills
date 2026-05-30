# Patch Tool: read_file Format Gotcha

## The Problem

When copying `old_string` from `read_file()` output to use with `patch()`,
the line-number prefix (`LINE_NUM|CONTENT`) gets confused with actual file
content. This causes extra `|` characters to be inserted into the file.

**Example — read_file output:**
```
    64|| `20260102_083000_123456` (full ID) | **Unnamed session** —...
```

The format is `LINE_NUM|CONTENT`. So the actual file content on line 64 is:
```
| `20260102_083000_123456` (full ID) | **Unnamed session** —...
```

Note: the content starts with `| ` (pipe + space) which is part of the
markdown table syntax. The `LINE_NUM|` prefix is NOT part of the content.

## The Mistake

Copying the line as shown in read_file output into `old_string`:

```python
patch(path="SKILL.md",
      old_string="|| `20260102_083000_123456` ...",  # WRONG — starts with ||
      new_string="...")
```

This adds an extra `|` because the old_string already had one `|` from the
content, plus another `|` from the line-number prefix that was mistakenly
included.

## The Fix

1. Read the file with `read_file()` to see the content
2. When copying `old_string`, mentally subtract the `LINE_NUM|` prefix
3. If the line shows `42|CONTENT`, your old_string should be `CONTENT`, not
   `|CONTENT` or `42|CONTENT`
4. For markdown tables where the content itself starts with `|`, use
   `old_string` starting with exactly one `|` (the table syntax pipe)

**Quick rule of thumb:** The first `|` in the read_file output is the
line-number separator. Everything after it is the actual file content, which
may itself contain `|` characters.

## Safer Alternative

Instead of copying from read_file output, use `search_files()` with
`output_mode="content"` to locate the exact text, or read a narrow range
with `read_file(offset=N, limit=5)` and manually strip the line numbers.

## Triple-Check Step

Before applying a patch where the old_string contains `|` characters:
1. Read the target lines with `read_file()`
2. Verify exactly which characters are content vs. line prefix
3. If unsure, read a smaller window or use `search_files()` for precise matching

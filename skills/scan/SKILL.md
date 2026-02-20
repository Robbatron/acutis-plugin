---
name: scan
description: Verify code for security vulnerabilities using Acutis PCST verification. Use when you've written or edited code that handles user input, generates HTML, or constructs SQL queries.
---

# Security Scan with Acutis

Scan code for CWE-79 (XSS) and CWE-89 (SQL Injection) using `mcp__acutis__scan_code`.

## How to Build a Contract

Analyze your code and declare:
- **Sources**: User-controlled data origins (e.g., `request.args.get`, `req.body`, `$_GET`)
- **Sinks**: Where data is output — use the right category:
  - **HTMLOutput**: `return` (HTML strings), `innerHTML`, `.html()`, `document.write()`
  - **SQLQuery**: `cursor.execute()`, `db.execute()`, `db.query()`
  - **SafeOutput**: `jsonify`, `json.dumps`, `textContent`, `.text()`, `print`, logging — anything that auto-escapes or isn't HTML/SQL
- **Transforms**: Only actual sanitizer **function calls** (not variables/sets/guards):
  - EscapesHTML: `html.escape()`, `escape()`, `escapeHtml()`
  - EscapesSQL: `mysql_real_escape_string()`
  - ParameterizesSQL: parameterized query calls like `cursor.execute(sql, (param,))`

## Call the Tool

```
mcp__acutis__scan_code({
  code: "<source code>",
  language: "python",
  contract: {
    sources: ["request.args.get"],
    sinks: [{"name": "return", "category": "HTMLOutput"}],
    transforms: [{"name": "html.escape", "effect": "EscapesHTML"}]
  }
})
```

## Critical Rules

1. **NEVER include witnesses** — they are always auto-inferred. Omit the `witnesses` field entirely.
2. **Transforms must be function calls** — allowlists, set checks, if-guards are control flow, NOT transforms. The scanner cannot trace control flow.
3. **Use SafeOutput liberally** — for `jsonify`, `json.dumps`, `print`, logging, and any function that doesn't interpret input as HTML or SQL.
4. **Keep contracts minimal** — only declare what's security-relevant.

## Handling Results

- **ALLOW**: Safe. Proceed.
- **BLOCK_VIOLATION**: Vulnerability found. Read remediation, fix code, re-scan.
- **BLOCK_INCOMPLETE**: Contract issue. Common fixes:
  - "missing coverage for X" → Add X as a sink. Use `SafeOutput` for non-security functions.
  - "missing witness coverage" → Do NOT write witnesses. Simplify your contract or restructure code so user input doesn't reach the sink through untraceable paths (f-strings, string formatting).

## Common Patterns

**Flask JSON endpoint** (safe — no XSS/SQLi vector):
```
sinks: [{"name": "jsonify", "category": "SafeOutput"}]
```

**Flask HTML response** (XSS risk):
```
sinks: [{"name": "return", "category": "HTMLOutput"}]
transforms: [{"name": "escape", "effect": "EscapesHTML"}]
```

**SQL query** (SQLi risk):
```
sinks: [{"name": "db.execute", "category": "SQLQuery"}]
```

**Dynamic ORDER BY / table names**: The scanner can't trace allowlist guards. Use a dictionary mapping user input to hardcoded SQL strings so user input never reaches the query.

## Quick Reference

| Field | Format | Example |
|-------|--------|---------|
| sources | `string[]` | `["request.args.get"]` |
| sinks | `{name, category}[]` | `[{"name": "db.execute", "category": "SQLQuery"}]` |
| transforms | `{name, effect}[]` | `[{"name": "html.escape", "effect": "EscapesHTML"}]` |

**Categories**: HTMLOutput, SQLQuery, JSONOutput, SafeOutput
**Effects**: EscapesHTML, EscapesSQL, ParameterizesSQL, DecodesURL, PreservesProperties
**Case-insensitive**. Omit witnesses — always.

---
name: scan
description: Verify code for security vulnerabilities using Acutis PCST verification. Use when you've written or edited code that handles user input, generates HTML, or constructs SQL queries.
---

# Security Scan with Acutis

Scan the current code for security vulnerabilities (CWE-79 XSS, CWE-89 SQL Injection) using the `mcp__acutis__scan_code` tool.

## Instructions

1. **Identify the code** to verify — focus on code you recently wrote or edited, especially anything handling user input, generating HTML, or constructing SQL queries.

2. **Build a PCST contract** by analyzing the code:
   - **Sources**: Variables or function calls that introduce user-controlled data (e.g., `request.args.get`, `req.body`, `$_GET`)
   - **Sinks**: Functions that output data in a security-sensitive context:
     - HTMLOutput: `innerHTML`, `.html()`, `document.write()`, `return` in HTML templates
     - SQLQuery: `cursor.execute()`, `db.query()`, `mysql_query()`
     - SafeOutput: `textContent`, `.text()`, parameterized queries
   - **Transforms**: Functions that sanitize data:
     - EscapesHTML: `html.escape()`, `escapeHtml()`
     - EscapesSQL: `mysql_real_escape_string()`
     - ParameterizesSQL: prepared statements with placeholders

3. **Call the scan tool** with the code and contract:

```
mcp__acutis__scan_code({
  code: "<the source code>",
  language: "python",  // or "javascript" or "php"
  contract: {
    sources: ["request.args.get"],
    sinks: [{"name": "return", "category": "HTMLOutput"}],
    transforms: [{"name": "html.escape", "effect": "EscapesHTML"}]
  }
})
```

4. **Act on the result**:
   - **ALLOW**: Code is safe. Proceed.
   - **BLOCK_VIOLATION**: Vulnerability found. Read the violation details and remediation guidance. Fix the code and re-scan.
   - **BLOCK_INCOMPLETE**: Contract issue. Check for missing sources, sinks, or transforms and re-scan.

## Contract Quick Reference

| Field | Format | Example |
|-------|--------|---------|
| sources | `string[]` | `["request.args.get", "req.body.name"]` |
| sinks | `{name, category}[]` | `[{"name": "return", "category": "HTMLOutput"}]` |
| transforms | `{name, effect}[]` | `[{"name": "html.escape", "effect": "EscapesHTML"}]` |

**Sink categories**: HTMLOutput, SQLQuery, JSONOutput, SafeOutput
**Transform effects**: EscapesHTML, EscapesSQL, ParameterizesSQL, DecodesURL, PreservesProperties

Witnesses are auto-inferred — omit them. Enum values are case-insensitive.

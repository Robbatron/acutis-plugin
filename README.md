# Acutis — Claude Code Plugin

Zero Trust security verification for AI-generated code. Automatically verifies code for **XSS (CWE-79)** and **SQL Injection (CWE-89)** vulnerabilities using formal property lattice verification.

## Install

```
/plugin marketplace add Robbatron/acutis-plugin
/plugin install acutis@acutis-plugin
```

That's it. The plugin connects to `mcp.acutis.dev` — no local dependencies beyond Python 3 (stdlib only, for the stop hook).

## What You Get

| Component | What it does |
|-----------|-------------|
| **MCP Server** | `scan_code` tool — takes code, language, and a PCST contract → returns ALLOW or BLOCK with proof artifacts |
| **Stop Hook** | Safety net — blocks the agent from finishing if it wrote security-relevant code without a `scan_code` ALLOW |
| **Scan Skill** | `/acutis:scan` — manual trigger with guided contract construction |

## How It Works

Acutis uses a **Type System Paradigm**: the AI declares security semantics (sources, sinks, transforms), and Acutis formally verifies them. No pattern databases, no heuristics — the AI provides all semantic information, Acutis provides formal verification.

### The Stop Hook (safety net)

The stop hook reads the session transcript and tracks **ordering**:

1. Walk transcript entries in order
2. Note each security-relevant Write/Edit (`.py`, `.js`, `.ts`, `.php`, `.html`)
3. Note each `scan_code` call that returned ALLOW
4. If the last ALLOW comes **after** the last Write → **allow stop** (already verified, invisible)
5. If the last Write comes **after** the last ALLOW → **block** (unverified code)

This means:
- If the agent proactively scans → the hook never fires, zero extra tokens
- If the agent forgets → the hook catches it with a short block message
- No redundant scans

The hook is a plain Python script (stdlib only) that runs once when the agent tries to stop.

### The scan_code Tool

```
scan_code(code: string, language: string, contract: PCST)
```

- `code` — the source code as a string
- `language` — `"python"`, `"javascript"`, or `"php"`
- `contract` — PCST contract declaring sources, sinks, and transforms

Returns: `ALLOW` (safe), `BLOCK_VIOLATION` (vulnerability found, with remediation), or `BLOCK_INCOMPLETE` (contract incomplete).

## Manage

```bash
# Disable without uninstalling
/plugin disable acutis@acutis-plugin

# Re-enable
/plugin enable acutis@acutis-plugin

# Completely remove
/plugin uninstall acutis@acutis-plugin

# Update to latest
/plugin marketplace update acutis-plugin
```

## Requirements

- **Claude Code v1.0.33+**
- **Python 3** (stdlib only — for the stop hook script)
- Internet connection (MCP server at `mcp.acutis.dev`)

## Plugin Structure

```
acutis-plugin/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest
│   └── marketplace.json     # Marketplace catalog
├── .mcp.json                # MCP server config (remote HTTP)
├── hooks/
│   └── hooks.json           # Stop hook configuration
├── skills/
│   └── scan/
│       └── SKILL.md         # /acutis:scan skill
├── scripts/
│   ├── stop-hook.sh         # Stop hook wrapper
│   └── stop-hook.py         # Stop hook implementation
└── README.md
```

## How the Stop Hook Works

```
Agent writes/edits security-relevant code
                │
                ▼
Agent tries to stop
                │
                ▼
Stop hook fires (reads transcript once)
┌────────────────────────────────────┐
│ Track ordering:                    │
│  • last security-relevant Write    │
│  • last scan_code ALLOW            │
│                                    │
│ ALLOW after Write? → allow stop    │
│ Write after ALLOW? → block         │
└────────────────────────────────────┘
                │
    ┌───────────┴───────────┐
    │                       │
Already verified      Unverified code
    │                       │
 ALLOW                   BLOCK
(invisible)     (agent must call scan_code)
```

## Links

- **Website**: [acutis.dev](https://acutis.dev)
- **MCP Server**: [mcp.acutis.dev](https://mcp.acutis.dev)
- **Main Repository**: [Robbatron/Acutis](https://github.com/Robbatron/Acutis)
- **License**: MIT

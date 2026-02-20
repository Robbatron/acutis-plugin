#!/usr/bin/env python3
"""
Acutis Stop Hook — safety net for Claude Code.

Blocks the agent from completing if it wrote security-relevant code
that hasn't been verified via scan_code. If the agent already called scan_code
and got ALLOW after its last edit, the hook is invisible.

The hook does NOT invoke Acutis directly — it only reads the transcript to
determine whether scan_code was called. The agent calls scan_code via MCP.

Hook protocol:
  - stdin: JSON with transcript_path, etc.
  - stdout: JSON response
  - exit 0: allow (parse stdout for JSON)
  - exit 2: blocking error
"""

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SECURITY_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".php",
    ".html", ".htm", ".mjs", ".cjs",
}

SKIP_PATTERNS = {
    "node_modules", "__pycache__", ".git", "venv", ".venv",
    "package-lock.json", "yarn.lock", "poetry.lock",
}

WRITE_TOOLS = {"Write", "Edit", "write", "edit", "editFiles", "createFile"}

SCAN_TOOL_NAMES = {"mcp__acutis__scan_code", "scan_code", "acutis__scan_code"}


def read_hook_input() -> dict:
    """Read the JSON hook input from stdin."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, IOError):
        return {}


def is_security_relevant(file_path: str) -> bool:
    """Check if a file path is security-relevant based on extension."""
    p = Path(file_path)
    if p.suffix.lower() not in SECURITY_EXTENSIONS:
        return False
    if set(p.parts) & SKIP_PATTERNS:
        return False
    return True


def analyze_transcript(transcript_path: str) -> tuple[bool, bool]:
    """Walk the transcript and determine verification state.

    Returns (has_unverified_writes, has_security_writes):
      - has_security_writes: any security-relevant file was written
      - has_unverified_writes: last security write comes AFTER last scan_code ALLOW
    """
    if not transcript_path or not os.path.isfile(transcript_path):
        return False, False

    last_security_write_idx = -1
    last_scan_allow_idx = -1
    idx = 0

    try:
        with open(transcript_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                writes, allow = _analyze_entry(entry)
                if writes:
                    last_security_write_idx = idx
                if allow:
                    last_scan_allow_idx = idx

                idx += 1
    except (IOError, PermissionError):
        pass

    has_security_writes = last_security_write_idx >= 0
    has_unverified_writes = last_security_write_idx > last_scan_allow_idx

    return has_unverified_writes, has_security_writes


def _analyze_entry(entry, _depth=0) -> tuple[bool, bool]:
    """Check a transcript entry for security-relevant writes and scan ALLOWs.

    Returns (has_security_write, has_scan_allow).
    """
    if _depth > 10:
        return False, False

    has_write = False
    has_allow = False

    if isinstance(entry, dict):
        # Check for Write/Edit tool_use
        if entry.get("type") == "tool_use" and entry.get("name") in WRITE_TOOLS:
            tool_input = entry.get("input", entry.get("tool_input", {}))
            fp = tool_input.get("file_path", tool_input.get("filePath", ""))
            if fp and is_security_relevant(fp):
                has_write = True

        if entry.get("tool_name") in WRITE_TOOLS:
            tool_input = entry.get("tool_input", {})
            fp = tool_input.get("file_path", tool_input.get("filePath", ""))
            if fp and is_security_relevant(fp):
                has_write = True

        # Check for scan_code tool_result with ALLOW
        if entry.get("type") == "tool_result" and entry.get("name") in SCAN_TOOL_NAMES:
            content = entry.get("content", "")
            if isinstance(content, str) and "ALLOW" in content:
                has_allow = True
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "ALLOW" in str(item.get("text", "")):
                        has_allow = True

        # Also check for scan_code in tool_name + result patterns
        if entry.get("tool_name") in SCAN_TOOL_NAMES:
            result = entry.get("result", entry.get("tool_result", ""))
            if isinstance(result, str) and "ALLOW" in result:
                has_allow = True
            elif isinstance(result, dict) and "ALLOW" in str(result.get("decision", "")):
                has_allow = True

        # Recurse into nested structures
        for key in ("content", "messages", "message"):
            val = entry.get(key)
            if isinstance(val, (dict, list)):
                w, a = _analyze_entry(val, _depth + 1)
                has_write = has_write or w
                has_allow = has_allow or a

    elif isinstance(entry, list):
        for item in entry:
            w, a = _analyze_entry(item, _depth + 1)
            has_write = has_write or w
            has_allow = has_allow or a

    return has_write, has_allow


def main() -> None:
    """Main hook entry point."""
    hook_input = read_hook_input()

    # Guard: prevent infinite loops (Claude Code sets stop_hook_active)
    if hook_input.get("stop_hook_active", False):
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")
    has_unverified, has_writes = analyze_transcript(transcript_path)

    if not has_writes or not has_unverified:
        # No security-relevant code, or already verified — allow stop
        sys.exit(0)

    # Block: unverified security-relevant code exists
    response = {
        "decision": "block",
        "reason": (
            "Security-relevant code was written but not yet verified. "
            "Call mcp__acutis__scan_code with the code and a PCST contract. "
            "Fix any BLOCK results before completing."
        ),
    }

    json.dump(response, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


if __name__ == "__main__":
    main()

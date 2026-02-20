#!/usr/bin/env bash
# Wrapper script for the Acutis Stop hook.
#
# Uses system python3 (stdlib only) — the stop hook has zero dependencies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

exec python3 "$SCRIPT_DIR/stop-hook.py" "$@"

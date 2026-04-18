#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_DOC="$ROOT_DIR/docs/notebooklm/EXECUTION_ARCHIVE.md"
GUARDRAIL_DOC="$ROOT_DIR/docs/notebooklm/GUARDRAIL.md"
FEATURE_MAP_DOC="$ROOT_DIR/docs/notebooklm/WONSEOKJUNG_FEATURE_MAP.md"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/notebooklm_guardrail.log"

cmd="${1:-unknown}"

mkdir -p "$LOG_DIR"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] cmd=$cmd" >> "$LOG_FILE"

echo "[Guardrail] Reference:"
echo "  - $ARCHIVE_DOC"
echo "  - $GUARDRAIL_DOC"
echo "  - $FEATURE_MAP_DOC"

if [[ ! -f "$FEATURE_MAP_DOC" ]]; then
  echo "[Guardrail][BLOCK] Missing feature map: $FEATURE_MAP_DOC"
  exit 1
fi

auth_cache="$HOME/.notebooklm-mcp/auth.json"
browser_state="$ROOT_DIR/skills/skills/notebooklm/data/browser_state/state.json"

if [[ "$cmd" != "setup" && "$cmd" != "reauth" && "$cmd" != "help" && "$cmd" != "-h" && "$cmd" != "--help" ]]; then
  if [[ ! -f "$auth_cache" ]]; then
    echo "[Guardrail][BLOCK] Missing auth cache: $auth_cache"
    echo "Run: .venv/bin/notebooklm-mcp-auth --port 9223"
    exit 1
  fi
fi

if [[ -f "$browser_state" ]]; then
  echo "[Guardrail] browser_state found."
else
  echo "[Guardrail][WARN] browser_state not found: $browser_state"
fi

echo "[Guardrail] Strategy: fast research first, deep research fallback only."
echo "[Guardrail] Keep long-query retries and save outputs step-by-step."
echo "[Guardrail][ENFORCE] NotebookLM-only execution is mandatory."
echo "[Guardrail][ENFORCE] On overload, reduce scope (topic count) instead of switching tools."
echo "[Guardrail][ENFORCE] Deep research is attempted first with extended timeout; fallback only on failure."
echo "[Guardrail][ENFORCE] Source floor per notebook: minimum 25 (use all if more are collected)."
echo "[Guardrail][ENFORCE] Plain-language intent must be interpreted via wonseokjung feature map before execution."
echo "[Guardrail][ENFORCE] Default deliverable must be created inside NotebookLM Studio (completed artifact)."
echo "[Guardrail][ENFORCE] For time-sensitive topics (e.g., AI), prioritize sources from the last 2 years."

# Hard policy env defaults (can be tightened by caller, but not relaxed)
export NOTEBOOKLM_ONLY="${NOTEBOOKLM_ONLY:-1}"
export NOTEBOOKLM_ADAPTIVE_LOAD="${NOTEBOOKLM_ADAPTIVE_LOAD:-1}"
export NOTEBOOKLM_OVERLOAD_LIMIT="${NOTEBOOKLM_OVERLOAD_LIMIT:-2}"
export NOTEBOOKLM_DEEP_FIRST="${NOTEBOOKLM_DEEP_FIRST:-1}"
export NOTEBOOKLM_DEEP_TIMEOUT="${NOTEBOOKLM_DEEP_TIMEOUT:-1200}"
export NOTEBOOKLM_MAX_SOURCES="${NOTEBOOKLM_MAX_SOURCES:-0}"
export NOTEBOOKLM_TARGET_SOURCES="${NOTEBOOKLM_TARGET_SOURCES:-25}"
export NOTEBOOKLM_RECENCY_WINDOW_YEARS="${NOTEBOOKLM_RECENCY_WINDOW_YEARS:-2}"
export NOTEBOOKLM_REQUIRE_STUDIO_ARTIFACT="${NOTEBOOKLM_REQUIRE_STUDIO_ARTIFACT:-1}"

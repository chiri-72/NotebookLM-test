#!/usr/bin/env bash
set -euo pipefail

# Convert plain-language intent into a concrete notebookLM command.
# Output format: command string

if [[ $# -lt 1 ]]; then
  echo ""
  exit 0
fi

intent="$*"
lower="$(printf '%s' "$intent" | tr '[:upper:]' '[:lower:]')"

if [[ "$lower" == *"status"* || "$lower" == *"상태"* || "$lower" == *"세션"* ]]; then
  echo "status"
  exit 0
fi

if [[ "$lower" == *"auth"* || "$lower" == *"login"* || "$lower" == *"로그인"* || "$lower" == *"인증"* ]]; then
  echo "setup"
  exit 0
fi

if [[ "$lower" == *"list"* || "$lower" == *"목록"* || "$lower" == *"notebook list"* || "$lower" == *"노트북 리스트"* ]]; then
  echo "list"
  exit 0
fi

# Research/query-like intent defaults to ask
if [[ "$lower" == *"research"* || "$lower" == *"딥리서치"* || "$lower" == *"리서치"* || "$lower" == *"질문"* || "$lower" == *"요약"* || "$lower" == *"정리"* || "$lower" == *"분석"* ]]; then
  echo "ask::$intent"
  exit 0
fi

# Fallback: treat as ask to keep within NotebookLM scope
echo "ask::$intent"

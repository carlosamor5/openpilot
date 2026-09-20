#!/usr/bin/env bash
# Comma hardware display-only demo. No Panda/control processes are allowed.
set -euo pipefail

export OPENPILOT_DISPLAY_ONLY_DEMO=1
export OPENPILOT_WHISPER_BIN="${OPENPILOT_WHISPER_BIN:-/data/voice-reporting/whisper-cli}"
export OPENPILOT_WHISPER_MODEL="${OPENPILOT_WHISPER_MODEL:-/data/voice-reporting/ggml-tiny.en-q5_1.bin}"
export OPENPILOT_REPORT_DIR="${OPENPILOT_REPORT_DIR:-/data/voice-reports}"

mkdir -p "$OPENPILOT_REPORT_DIR"
exec ./launch_openpilot.sh

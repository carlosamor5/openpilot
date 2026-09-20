#!/usr/bin/env bash
# Non-destructive comma4 deployment preflight.
# Usage: tools/comma4_preflight.sh comma@<device-ip>
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 comma@<device-ip>" >&2
  exit 2
fi

TARGET="$1"
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=8 "$TARGET")

printf 'Checking SSH access to %s...\n' "$TARGET"
"${SSH[@]}" 'set -eu
  echo "--- identity ---"
  id
  hostname || true
  echo "--- hardware markers ---"
  test -f /TICI && echo /TICI=present || echo /TICI=missing
  test -f /AGNOS && echo /AGNOS=present || echo /AGNOS=missing
  echo "--- device model ---"
  if test -r /sys/firmware/devicetree/base/model; then
    tr -d "\000" < /sys/firmware/devicetree/base/model
    echo
  else
    echo unavailable
  fi
  echo "--- version ---"
  test -r /VERSION && cat /VERSION || echo unavailable
  echo "--- storage ---"
  df -h /data /data/openpilot 2>/dev/null || df -h / || true
  echo "--- active installation ---"
  if test -d /data/openpilot; then
    readlink -f /data/openpilot || true
    git -C /data/openpilot rev-parse HEAD 2>/dev/null || true
  else
    echo /data/openpilot=missing
  fi
  echo "--- audio capture devices ---"
  if command -v arecord >/dev/null 2>&1; then arecord -l || true; else echo arecord=missing; fi
  echo "--- audio utilities ---"
  command -v python3 || true
  command -v arecord || true
  command -v aplay || true
  echo "--- safety ---"
  echo "No files were changed by this preflight."
'

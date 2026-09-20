#!/usr/bin/env bash
# Guarded, reversible deployment helper.
# It never changes a device unless --apply is provided.
set -euo pipefail

APPLY=0
TARGET=""
REMOTE_ROOT="/data/openpilot-voice-reporting-staged"
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --target=*) TARGET="${arg#*=}" ;;
    --remote-root=*) REMOTE_ROOT="${arg#*=}" ;;
    --help|-h)
      echo "Usage: $0 --target=comma@<ip> [--apply] [--remote-root=/data/openpilot-voice-reporting-staged]"
      exit 0
      ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "Missing --target=comma@<device-ip>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=8 "$TARGET")
RSYNC=(rsync -av --progress --exclude=.git --exclude=.venv --exclude=reports --exclude=backups)

"$ROOT/tools/comma4_preflight.sh" "$TARGET"

if [[ "$APPLY" != 1 ]]; then
  echo
  echo "DRY RUN ONLY: no device files were changed."
  echo "Review the hardware/model/audio output above."
  echo "To stage after review, rerun with:"
  echo "  $0 --target=$TARGET --apply"
  exit 0
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/data/openpilot-backup-voice-reporting-$STAMP.tgz"

echo "Creating remote backup: $BACKUP"
"${SSH[@]}" "set -eu; test -d /data/openpilot; tar -czf '$BACKUP' -C /data openpilot"

echo "Copying deployment into staging directory: $REMOTE_ROOT"
"${SSH[@]}" "rm -rf '$REMOTE_ROOT'; mkdir -p '$REMOTE_ROOT'"
"${RSYNC[@]}" "$ROOT/" "$TARGET:$REMOTE_ROOT/"

"${SSH[@]}" "set -eu; test -f '$REMOTE_ROOT/launch_openpilot.sh'; test -f '$REMOTE_ROOT/mici_onroad_harness.py'; echo 'Staging verified: $REMOTE_ROOT'; echo 'Backup: $BACKUP'"
echo "Deployment staged only; active /data/openpilot was not replaced."
echo "Do not switch the active installation until target-specific tests pass."

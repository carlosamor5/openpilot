#!/usr/bin/env python3
"""Create a self-contained backup of the known-good hackathon demo files."""
from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

FILES = (
  "mici_onroad_harness.py",
  "selfdrive/ui/layouts/main.py",
  "selfdrive/ui/onroad/augmented_road_view.py",
  "selfdrive/ui/mici/onroad/model_renderer.py",
  "selfdrive/ui/report_view.py",
  "selfdrive/reporting/__init__.py",
  "selfdrive/reporting/models.py",
  "selfdrive/reporting/service.py",
  "selfdrive/reporting/tagger.py",
  "system/ui/lib/wifi_manager.py",
  "tools/hackathon_demo.py",
  "run_hackathon_demo.bat",
)


def sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def main() -> int:
  repo = Path(__file__).resolve().parents[1]
  stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
  destination = repo / "backups" / f"hackathon-demo-{stamp}"
  manifest: list[str] = [f"backup_created_utc={stamp}", ""]

  for relative in FILES:
    source = repo / relative
    if not source.is_file():
      raise SystemExit(f"Missing demo file: {source}")
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    manifest.append(f"{sha256(target)}  {relative}")

  (destination / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n", encoding="utf-8")
  print(f"Created backup: {destination}")
  print(f"Manifest: {destination / 'MANIFEST.sha256'}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())

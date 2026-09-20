#!/usr/bin/env python3
"""Launch the protected hackathon replay configuration.

This is intentionally a small, deterministic wrapper around mici_onroad_harness.py.
It verifies the local replay/model assets before starting the demo UI.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_ROUTE = "5beb9b58bd12b691|0000010a--a51155e496"
DEFAULT_DATA_DIR = "/mnt/d/comma_ai/offline_data/replay_routes"
DEFAULT_MODEL = "/mnt/d/comma_ai/whisper.cpp/models/ggml-tiny.en.bin"
DEFAULT_WHISPER = "/mnt/d/comma_ai/whisper.cpp/build/bin/whisper-cli"


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Run the protected hackathon replay demo")
  parser.add_argument("--route", default=DEFAULT_ROUTE)
  parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
  parser.add_argument("--camera", choices=("road", "wide"), default="road")
  parser.add_argument("--start", type=int, default=0)
  parser.add_argument("--playback", type=float, default=1.0)
  return parser.parse_args()


def require_file(path: str, label: str) -> None:
  if not Path(path).is_file():
    raise SystemExit(f"Missing {label}: {path}")


def main() -> int:
  args = parse_args()
  repo = Path(__file__).resolve().parents[1]
  harness = repo / "mici_onroad_harness.py"
  replay = repo / "tools" / "replay" / "replay"
  data_dir = Path(args.data_dir)
  whisper = os.environ.get("OPENPILOT_WHISPER_BIN", DEFAULT_WHISPER)
  model = os.environ.get("OPENPILOT_WHISPER_MODEL", DEFAULT_MODEL)
  report_dir = Path(os.environ.get("OPENPILOT_REPORT_DIR", str(repo / "reports")))

  require_file(str(harness), "replay harness")
  require_file(str(replay), "replay executable")
  require_file(whisper, "whisper.cpp executable")
  require_file(model, "Whisper model")
  if not data_dir.is_dir():
    raise SystemExit(f"Missing replay data directory: {data_dir}")
  report_dir.mkdir(parents=True, exist_ok=True)

  env = os.environ.copy()
  env.update({
    "PYTHONPATH": f"{repo / 'opendbc_repo'}:{repo}:{env.get('PYTHONPATH', '')}",
    "WINDOWED": "1",
    "GALLIUM_DRIVER": "d3d12",
    "WAYLAND_DISPLAY": "",
    "XDG_SESSION_TYPE": "x11",
    "DISPLAY": ":0",
    "LIBGL_ALWAYS_SOFTWARE": "1",
    "OPENPILOT_WHISPER_BIN": whisper,
    "OPENPILOT_WHISPER_MODEL": model,
    "OPENPILOT_REPORT_DIR": str(report_dir),
  })

  command = [sys.executable, "-u", str(harness), args.route,
             "--data_dir", str(data_dir), "--camera", args.camera,
             "--start", str(args.start), "--playback", str(args.playback)]
  print("Starting protected hackathon replay demo")
  print(f"Route: {args.route}")
  print(f"Reports: {report_dir}")
  print("Press Ctrl+C to stop.")
  return subprocess.call(command, cwd=repo, env=env)


if __name__ == "__main__":
  raise SystemExit(main())

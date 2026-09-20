from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
import wave
from pathlib import Path

from .models import Report, Transcript
from .tagger import classify, summarize

SAMPLE_RATE = 16_000


class ReportService:
  """Small platform-neutral voice report service using whisper.cpp."""

  def __init__(self, root: str | None = None):
    self.root = Path(root or os.environ.get("OPENPILOT_REPORT_DIR", "/tmp/openpilot_reports"))
    self.model = os.environ.get("OPENPILOT_WHISPER_MODEL", "")
    self.binary = os.environ.get("OPENPILOT_WHISPER_BIN", "whisper-cli")
    self._lock = threading.Lock()
    self._recording = False
    self._samples: list[bytes] = []
    self._stream = None
    self._worker: threading.Thread | None = None
    self.status = "idle"
    self.report: Report | None = None
    self.error: str = ""

  @property
  def recording(self) -> bool:
    return self._recording

  def start(self) -> bool:
    if self._recording or self.status == "processing":
      return False
    try:
      import sounddevice as sd
      self._samples = []
      self.error = ""
      self.status = "recording"
      self._recording = True
      self._stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=800,
        callback=lambda data, frames, time_info, status: self._samples.append(data.tobytes()),
      )
      self._stream.start()
      return True
    except Exception as exc:
      self._recording = False
      self.status = "error"
      self.error = f"Microphone unavailable: {exc}"
      return False

  def stop(self) -> bool:
    if not self._recording:
      return False
    self._recording = False
    try:
      if self._stream is not None:
        self._stream.stop()
        self._stream.close()
      self._stream = None
      pcm = b"".join(self._samples)
      self.status = "processing"
      self._worker = threading.Thread(target=self._process, args=(pcm,), daemon=True)
      self._worker.start()
      return True
    except Exception as exc:
      self.status = "error"
      self.error = str(exc)
      return False

  def toggle(self) -> None:
    self.stop() if self._recording else self.start()

  def _process(self, pcm: bytes) -> None:
    try:
      self.root.mkdir(parents=True, exist_ok=True)
      with tempfile.TemporaryDirectory(prefix="openpilot-report-") as directory:
        wav_path = Path(directory) / "recording.wav"
        self._write_wav(wav_path, pcm)
        transcript = self._transcribe(wav_path)
      tags = classify(transcript.text)
      report = Report(
        transcript=transcript.text,
        summary=summarize(transcript.text, tags),
        categories=tags,
        backend=transcript.backend,
        model=transcript.model,
      )
      output = self.root / f"{report.created_at.replace(':', '-')}.json"
      output.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
      with self._lock:
        self.report = report
        self.status = "ready"
    except Exception as exc:
      with self._lock:
        self.status = "error"
        self.error = str(exc)

  def _transcribe(self, wav_path: Path) -> Transcript:
    if not self.model:
      raise RuntimeError("Set OPENPILOT_WHISPER_MODEL to a ggml whisper.cpp model path")
    binary = shutil.which(self.binary) or self.binary
    result = subprocess.run(
      [binary, "-m", self.model, "-f", str(wav_path), "-nt", "-l", "en"],
      capture_output=True, text=True, timeout=120, check=True,
    )
    text = " ".join(line.strip() for line in result.stdout.splitlines() if line.strip())
    return Transcript(text=text, backend="whisper.cpp", model=self.model)

  @staticmethod
  def _write_wav(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as output:
      output.setnchannels(1)
      output.setsampwidth(2)
      output.setframerate(SAMPLE_RATE)
      output.writeframes(pcm)

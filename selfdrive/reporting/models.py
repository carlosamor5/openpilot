from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Transcript:
  text: str
  language: str = "en"
  backend: str = "whisper.cpp"
  model: str = ""


@dataclass(frozen=True)
class ReportTag:
  name: str
  confidence: float


@dataclass(frozen=True)
class Report:
  transcript: str
  summary: str
  categories: list[ReportTag] = field(default_factory=list)
  created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
  audio_file: str = ""
  backend: str = "whisper.cpp"
  model: str = ""

  def to_dict(self) -> dict[str, Any]:
    return asdict(self)

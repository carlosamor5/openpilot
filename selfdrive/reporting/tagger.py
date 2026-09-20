from __future__ import annotations

import re

from .models import ReportTag

_RULES = {
  "Safety Concern": ("danger", "dangerous", "unsafe", "near miss", "almost hit", "collision", "emergency"),
  "Lateral Control": ("lane", "drift", "center line", "steering", "steer", "curve", "left", "right"),
  "Longitudinal Control": ("brake", "braking", "accelerat", "following distance", "stop", "stopped"),
  "Perception": ("see", "missed", "detection", "detected", "obstacle", "vehicle", "traffic light"),
  "Planning/Behavior": ("merge", "hesitat", "maneuver", "decision", "route"),
  "Driver Interaction": ("takeover", "override", "grabbed the wheel", "disengage"),
  "Comfort": ("jerky", "rough", "uncomfortable", "harsh", "smooth"),
  "Vehicle/UI/Environment": ("camera", "sensor", "screen", "button", "rain", "construction", "road marking"),
}


def classify(text: str) -> list[ReportTag]:
  normalized = re.sub(r"[^a-z0-9 ]", " ", text.lower())
  tags: list[ReportTag] = []
  for name, keywords in _RULES.items():
    hits = sum(keyword in normalized for keyword in keywords)
    if hits:
      confidence = min(0.99, 0.55 + 0.12 * hits)
      tags.append(ReportTag(name, round(confidence, 2)))
  return sorted(tags, key=lambda tag: tag.confidence, reverse=True)


def summarize(text: str, tags: list[ReportTag]) -> str:
  clean = " ".join(text.split()).strip()
  if not clean:
    return "No speech was detected."
  if not tags:
    return clean[:160]
  category = tags[0].name.lower()
  sentence = clean[0].upper() + clean[1:] if clean else clean
  return f"Possible {category} issue: {sentence[:130]}"

from __future__ import annotations

import math

import pyray as rl

from openpilot.selfdrive.reporting.service import ReportService
from openpilot.system.ui.lib.application import FontWeight, gui_app


class ReportView:
  """Small on-road voice-report control and result overlay."""

  BUTTON_SIZE = 112
  MARGIN = 36

  def __init__(self):
    self.service = ReportService()
    self._button = rl.Rectangle(0, 0, self.BUTTON_SIZE, self.BUTTON_SIZE)
    self._pulse_started = 0.0

  def handle_mouse(self, mouse_pos: rl.Vector2, rect: rl.Rectangle) -> bool:
    x = rect.x + rect.width - self.MARGIN - self.BUTTON_SIZE
    y = rect.y + rect.height - self.MARGIN - self.BUTTON_SIZE
    self._button = rl.Rectangle(x, y, self.BUTTON_SIZE, self.BUTTON_SIZE)
    if rl.check_collision_point_rec(mouse_pos, self._button):
      self.service.toggle()
      return True
    return False

  def render(self, rect: rl.Rectangle) -> None:
    x = rect.x + rect.width - self.MARGIN - self.BUTTON_SIZE
    y = rect.y + rect.height - self.MARGIN - self.BUTTON_SIZE
    self._button = rl.Rectangle(x, y, self.BUTTON_SIZE, self.BUTTON_SIZE)
    recording = self.service.recording
    color = rl.Color(210, 45, 55, 245) if recording else rl.Color(246, 196, 0, 245)
    if recording:
      age = rl.get_time()
      pulse = 6 * math.sin(age * 3.14159265)
      rl.draw_circle(int(x + self.BUTTON_SIZE / 2), int(y + self.BUTTON_SIZE / 2), self.BUTTON_SIZE / 2 + pulse, color)
      rl.draw_circle(int(x + self.BUTTON_SIZE / 2), int(y + self.BUTTON_SIZE / 2), 13, rl.WHITE)
    else:
      rl.draw_circle(int(x + self.BUTTON_SIZE / 2), int(y + self.BUTTON_SIZE / 2), self.BUTTON_SIZE / 2, color)
      font = gui_app.font(FontWeight.SEMI_BOLD)
      rl.draw_text_ex(font, "R", rl.Vector2(x + 38, y + 23), 54, 0, rl.BLACK)

    status = self.service.status
    if status in ("recording", "processing", "ready", "error"):
      text = {
        "recording": "RECORDING",
        "processing": "TRANSCRIBING",
        "ready": "REPORT READY",
        "error": "REPORT ERROR",
      }[status]
      font = gui_app.font(FontWeight.SEMI_BOLD)
      label_width = rl.measure_text_ex(font, text, 28, 0).x
      label_x = rect.x + rect.width - self.MARGIN - label_width
      rl.draw_text_ex(font, text, rl.Vector2(label_x, y - 38), 28, 0, rl.WHITE)

    if self.service.report is not None and status == "ready":
      report = self.service.report
      panel = rl.Rectangle(rect.x + 48, rect.y + rect.height - 290, rect.width - 96, 220)
      rl.draw_rectangle_rounded(panel, 0.04, 12, rl.Color(0, 0, 0, 215))
      font = gui_app.font(FontWeight.SEMI_BOLD)
      rl.draw_text_ex(font, "VOICE REPORT", rl.Vector2(panel.x + 24, panel.y + 22), 30, 0, rl.WHITE)
      rl.draw_text_ex(font, report.summary[:110], rl.Vector2(panel.x + 24, panel.y + 70), 28, 0, rl.WHITE)
      tags = ", ".join(tag.name for tag in report.categories) or "Uncategorized"
      rl.draw_text_ex(font, f"Tags: {tags}", rl.Vector2(panel.x + 24, panel.y + 125), 24, rl.Color(246, 196, 0, 255))

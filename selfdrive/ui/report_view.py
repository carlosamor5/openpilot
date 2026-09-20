from __future__ import annotations

import math
import time

import pyray as rl

from openpilot.selfdrive.reporting.service import ReportService
from openpilot.system.ui.lib.application import FontWeight, gui_app


class ReportView:
  """Small on-road voice-report control and result overlay."""

  BUTTON_SIZE = 88
  # Keep the button clear of the lower-right edge by the same amount
  # horizontally and vertically.
  MARGIN = 50
  REPORT_TIMEOUT_SECONDS = 15.0

  def __init__(self):
    self.service = ReportService()
    self._button = rl.Rectangle(0, 0, self.BUTTON_SIZE, self.BUTTON_SIZE)
    self._pulse_started = 0.0
    self._report_visible_until = 0.0
    self._microphone = gui_app.texture("icons_mici/microphone.png", 42, 42)

  def handle_mouse(self, mouse_pos: rl.Vector2, rect: rl.Rectangle) -> bool:
    x = rect.x + rect.width - self.MARGIN - self.BUTTON_SIZE
    y = rect.y + rect.height - self.MARGIN - self.BUTTON_SIZE
    self._button = rl.Rectangle(x, y, self.BUTTON_SIZE, self.BUTTON_SIZE)
    if rl.check_collision_point_rec(mouse_pos, self._button):
      if self.service.status == "ready":
        self._report_visible_until = 0.0
        self.service.report = None
        self.service.status = "idle"
      else:
        self.service.toggle()
      return True
    return False

  def render(self, rect: rl.Rectangle) -> None:
    x = rect.x + rect.width - self.MARGIN - self.BUTTON_SIZE
    y = rect.y + rect.height - self.MARGIN - self.BUTTON_SIZE
    self._button = rl.Rectangle(x, y, self.BUTTON_SIZE, self.BUTTON_SIZE)
    recording = self.service.recording
    if self.service.status == "ready" and self._report_visible_until == 0.0:
      self._report_visible_until = time.monotonic() + self.REPORT_TIMEOUT_SECONDS
    if self._report_visible_until and time.monotonic() >= self._report_visible_until:
      self._report_visible_until = 0.0
      self.service.report = None
      self.service.status = "idle"
    color = rl.Color(210, 45, 55, 128) if recording else rl.Color(246, 196, 0, 128)
    if recording:
      age = rl.get_time()
      pulse = 6 * math.sin(age * 3.14159265)
      rl.draw_circle(int(x + self.BUTTON_SIZE / 2), int(y + self.BUTTON_SIZE / 2), self.BUTTON_SIZE / 2 + pulse, color)
      rl.draw_circle(int(x + self.BUTTON_SIZE / 2), int(y + self.BUTTON_SIZE / 2), 13, rl.WHITE)
    else:
      center = rl.Vector2(x + self.BUTTON_SIZE / 2, y + self.BUTTON_SIZE / 2)
      # Use one centered button with a subtle vertical yellow gradient.
      rl.draw_circle_gradient(
        center, self.BUTTON_SIZE / 2 - 2,
        rl.Color(255, 226, 62, 128), rl.Color(218, 158, 0, 128),
      )
      icon_x = center.x - self._microphone.width / 2
      icon_y = center.y - self._microphone.height / 2
      rl.draw_texture_ex(self._microphone, rl.Vector2(icon_x, icon_y), 0.0, 1.0, rl.Color(0, 0, 0, 128))

    status = self.service.status
    if status in ("recording", "processing", "ready", "error"):
      text = {
        "recording": "RECORDING",
        "processing": "TRANSCRIBING",
        "ready": "REPORT READY",
        "error": "REPORT ERROR",
      }[status]
      font = gui_app.font(FontWeight.SEMI_BOLD)
      label_width = rl.measure_text_ex(font, text, 14, 0).x
      # Leave extra room from the right edge so the full status label is visible.
      label_x = rect.x + rect.width - self.MARGIN - label_width - 12
      rl.draw_text_ex(font, text, rl.Vector2(label_x, y - 22), 14, 0, rl.WHITE)

    if self.service.report is not None and status == "ready" and self._report_visible_until:
      report = self.service.report
      panel = rl.Rectangle(rect.x + 90, rect.y + rect.height - 210, rect.width - 180, 145)
      rl.draw_rectangle_rounded(panel, 0.04, 12, rl.Color(0, 0, 0, 165))
      font = gui_app.font(FontWeight.SEMI_BOLD)
      rl.draw_text_ex(font, "VOICE REPORT", rl.Vector2(panel.x + 16, panel.y + 14), 19, 0, rl.WHITE)

      # Keep long summaries inside the panel and scroll them horizontally.
      summary = report.summary[:180]
      summary_size = rl.measure_text_ex(font, summary, 17, 0)
      summary_left = panel.x + 16
      summary_top = panel.y + 45
      summary_width = panel.width - 32
      rl.begin_scissor_mode(int(summary_left), int(summary_top), int(summary_width), 28)
      if summary_size.x <= summary_width:
        summary_x = summary_left
      else:
        cycle = summary_size.x + summary_width + 60
        offset = (time.monotonic() * 32) % cycle
        summary_x = summary_left + summary_width - offset
      rl.draw_text_ex(font, summary, rl.Vector2(summary_x, summary_top), 17, 0, rl.WHITE)
      rl.end_scissor_mode()

      tags = ", ".join(tag.name for tag in report.categories) or "Uncategorized"
      rl.draw_text_ex(font, f"Tags: {tags}", rl.Vector2(panel.x + 16, panel.y + 98), 16, 0, rl.Color(246, 196, 0, 255))

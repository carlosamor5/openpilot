"""Offline voice-reporting support for the openpilot UI."""

from .models import Report, Transcript
from .service import ReportService

__all__ = ["Report", "Transcript", "ReportService"]

#!/usr/bin/env python3
"""Write REPORT clips from micd's existing rawAudioData stream."""
import os
import time
import wave
from pathlib import Path
import cereal.messaging as messaging
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware.hw import Paths

SAMPLE_RATE = 16000

class ReportAudioRecorder:
  def __init__(self, params=None, root=None):
    self.params = params or Params()
    self.root = Path(root or Paths.log_root())
    self.wav = None
    self.tmp = None
    self.final = None

  def start(self):
    if self.wav is not None:
      return
    route = self.params.get("CurrentRoute")
    if not route:
      cloudlog.warning("REPORT audio unavailable: CurrentRoute is unset")
      return
    directory = self.root / route / "report_audio"
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"report-{time.strftime('%Y%m%d-%H%M%S')}-{time.monotonic_ns()}"
    self.tmp, self.final = directory / f".{stem}.wav.partial", directory / f"{stem}.wav"
    try:
      self.wav = wave.open(str(self.tmp), "wb")
      self.wav.setnchannels(1)
      self.wav.setsampwidth(2)
      self.wav.setframerate(SAMPLE_RATE)
    except OSError:
      cloudlog.exception("Could not open REPORT WAV")
      self.wav = self.tmp = self.final = None

  def stop(self):
    if self.wav is None:
      return
    wav, tmp, final = self.wav, self.tmp, self.final
    self.wav = self.tmp = self.final = None
    try:
      wav.close()
      os.replace(tmp, final)
    except OSError:
      cloudlog.exception("Could not finalize REPORT WAV")
      if tmp:
        tmp.unlink(missing_ok=True)

  def append(self, data, sample_rate):
    if self.wav is not None and sample_rate == SAMPLE_RATE:
      try:
        self.wav.writeframesraw(bytes(data))
      except OSError:
        cloudlog.exception("Could not write REPORT WAV")
        self.stop()

  def run(self):
    sm = messaging.SubMaster(["bookmarkButton", "rawAudioData"])
    while True:
      sm.update(100)
      if sm.updated["bookmarkButton"] and sm["bookmarkButton"].recordingCommand:
        if sm["bookmarkButton"].recordingActive:
          self.start()
        else:
          self.stop()
      if sm.updated["rawAudioData"]:
        audio = sm["rawAudioData"]
        self.append(audio.data, audio.sampleRate)

def main():
  ReportAudioRecorder().run()

if __name__ == "__main__":
  main()

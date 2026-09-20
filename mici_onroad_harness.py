#!/usr/bin/env python3
"""Visible stock openpilot on-road UI harness with replay video."""
from __future__ import annotations

import argparse
import math
import os
import signal
import subprocess
import time

import pyray as rl
from cereal import car, log, messaging
from openpilot.common.prefix import OpenpilotPrefix
from openpilot.common.api import Api
from openpilot.common.basedir import BASEDIR
from openpilot.common.params import Params
from openpilot.system.version import terms_version, training_version


def setup_calibration_params() -> None:
    params = Params()
    calibration = messaging.new_message("liveCalibration")
    calibration.liveCalibration.calStatus = log.LiveCalibrationData.Status.calibrated
    calibration.liveCalibration.rpyCalib = [0.0, math.radians(2.5), math.radians(-1.2)]
    params.put("CalibrationParams", calibration.to_bytes(), block=True)


def setup_developer_params() -> None:
    car_params = car.CarParams()
    car_params.alphaLongitudinalAvailable = True
    Params().put("CarParamsPersistent", car_params.to_bytes(), block=True)


def setup_state() -> None:
    params = Params()
    params.put("HasAcceptedTerms", terms_version, block=True)
    params.put("CompletedTrainingVersion", training_version, block=True)
    params.put("DongleId", "test123456789", block=True)
    params.put("Version", "0.11.1", block=True)
    params.put("GitBranch", "feature/carlosthon-report-release-mici", block=True)
    params.put("GitCommit", "70e157462304e5ce7d03ffbec6cb7f45bf347bb7", block=True)
    params.put("GitCommitDate", "stable release-mici", block=True)
    Api.get_token = lambda self, payload_extra=None, expiry_hours=0: "test_token"

DURATION_SECONDS = 600
FPS = 60
HARNESS_PREFIX = "mici_onroad_harness"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Mici UI with a replay camera stream")
    parser.add_argument("route", help="Replay route, for example 5beb9b58bd12b691|0000010a--a51155e496")
    parser.add_argument("--data_dir", required=True, help="Directory containing replay route data")
    parser.add_argument("--camera", choices=("road", "wide"), default="road")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--playback", type=float, default=1.0)
    return parser.parse_args()


def start_replay(args: argparse.Namespace) -> subprocess.Popen:
    command = [
        os.path.join(os.path.dirname(__file__), "tools/replay/replay"),
        args.route,
        "--data_dir", args.data_dir,
        "--prefix", HARNESS_PREFIX,
        "--start", str(args.start),
        "--playback", str(args.playback),
        "--no-hw-decoder",
        "--block", "deviceState,pandaStates,driverStateV2,selfdriveState,carState",
    ]
    if args.camera == "wide":
        command.append("--ecam")
    return subprocess.Popen(command, env={**os.environ, "OPENPILOT_PREFIX": HARNESS_PREFIX})


def main(args: argparse.Namespace) -> None:
    setup_state()
    setup_calibration_params()
    setup_developer_params()

    from openpilot.selfdrive.ui.ui_state import device, ui_state
    from openpilot.system.ui.lib.application import gui_app
    from openpilot.selfdrive.ui.layouts.main import MainLayout
    from msgq.visionipc import VisionStreamType

    gui_app.init_window("Carlosthon · OpenPilot On-road", fps=FPS)
    stream = VisionStreamType.VISION_STREAM_WIDE_ROAD if args.camera == "wide" else VisionStreamType.VISION_STREAM_ROAD
    MainLayout(camera_stream=stream)
    device.set_override_interactive_timeout(99999)

    replay_process = start_replay(args)
    pm = messaging.PubMaster(["deviceState", "pandaStates", "driverStateV2", "selfdriveState", "carState"])
    started_at = time.monotonic()
    print("Mici on-road harness started")
    print("The on-road camera page should appear after the startup transition.")
    print("REPORT button is in the upper-right of the on-road view.")
    print("Press Ctrl+C in this terminal to stop early.")

    try:
        for _ in gui_app.render():
            device_state = messaging.new_message("deviceState")
            device_state.deviceState.started = True
            # Replay routes may report an OS04C10 sensor. Use a supported
            # simulated device profile so the UI can select camera intrinsics.
            device_state.deviceState.deviceType = "tici"
            device_state.deviceState.networkType = log.DeviceState.NetworkType.wifi
            pm.send("deviceState", device_state)

            panda = messaging.new_message("pandaStates", 1)
            panda.pandaStates[0].pandaType = log.PandaState.PandaType.dos
            panda.pandaStates[0].ignitionLine = True
            pm.send("pandaStates", panda)

            selfdrive = messaging.new_message("selfdriveState")
            selfdrive.selfdriveState.enabled = False
            pm.send("selfdriveState", selfdrive)

            ui_state.update()
            if time.monotonic() - started_at >= DURATION_SECONDS:
                break
    finally:
        if replay_process.poll() is None:
            replay_process.send_signal(signal.SIGINT)
            try:
                replay_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                replay_process.kill()
                replay_process.wait()
        gui_app.close()
        print("Mici on-road harness finished")


if __name__ == "__main__":
    with OpenpilotPrefix(HARNESS_PREFIX):
        main(parse_args())

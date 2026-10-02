"""Manual push-to-talk capture on the Raspberry Pi.

The project has to be installed, and this machine needs the button and the
USB microphone. Example::

    voicestock-pi-ptt --pin 17 --bounce-time 0.05 \\
        --input-device "USB Audio" --output-directory recordings
"""

import argparse
import sys
import threading
from pathlib import Path

from pi.audio.capture import AudioCapture
from pi.audio.config import AudioCaptureConfig
from pi.audio.errors import AudioCaptureError
from pi.audio.sounddevice_backend import SoundDeviceBackend
from pi.input.push_to_talk_button import PushToTalkButton
from pi.push_to_talk.controller import (
    DEFAULT_MAX_DURATION_SECONDS,
    PushToTalkController,
)
from pi.push_to_talk.result import AudioCaptureResult


def main(argv: list[str] | None = None) -> int:
    """Run one push-to-talk session until Ctrl+C."""
    parser = argparse.ArgumentParser(description="Push-to-talk capture")
    parser.add_argument("--pin", type=int, required=True, help="BCM GPIO pin")
    parser.add_argument(
        "--bounce-time",
        type=float,
        required=True,
        help="button debounce time in seconds",
    )
    parser.add_argument(
        "--input-device",
        required=True,
        help="microphone name query, not a PortAudio index",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        required=True,
        help="directory for published WAV files",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=DEFAULT_MAX_DURATION_SECONDS,
        help="maximum recording length in seconds",
    )
    args = parser.parse_args(argv)

    config = AudioCaptureConfig(
        input_device=args.input_device,
        output_directory=args.output_directory,
    )
    capture = AudioCapture(config, SoundDeviceBackend(config.input_device))
    controller = PushToTalkController(
        capture,
        on_capture_completed=_print_result,
        on_capture_error=_print_error,
        max_duration=args.max_duration,
    )
    button = PushToTalkButton(
        args.pin,
        args.bounce_time,
        on_pressed=controller.notify_pressed,
        on_released=controller.notify_released,
    )
    controller.start()
    print("Waiting for the push-to-talk button. Press Ctrl+C to quit.", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print(file=sys.stderr)
    finally:
        button.close()
        controller.close()
    return 0


def _print_result(result: AudioCaptureResult) -> None:
    audio_format = result.format
    print("Capture completed", flush=True)
    print(f"Artifact ID: {result.artifact.id}", flush=True)
    print(f"Path: {result.artifact.path}", flush=True)
    print(f"Duration: {result.duration:.3f}s", flush=True)
    print(f"Termination: {result.termination_reason.name}", flush=True)
    print(
        "Format: "
        f"{audio_format.container} / {audio_format.sample_rate_hz / 1000:g} kHz / "
        f"mono / {audio_format.sample_width_bytes * 8}-bit",
        flush=True,
    )


def _print_error(error: AudioCaptureError) -> None:
    print(f"Capture error: {error}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())

"""Manual push-to-talk capture on the Raspberry Pi.

The project has to be installed, and this machine needs the button and the
USB microphone. Example::

    voicestock-pi-ptt --pin 17 --bounce-time 0.05 \\
        --input-device "USB Audio" --output-directory recordings

With ``--send-to-pc`` each recording is also sent to the PC configured by
``VOICESTOCK_PC_URL`` and ``VOICESTOCK_PC_TIMEOUT``, and the answer is printed.
"""

import argparse
import sys
import threading
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path

from pi.audio.capture import AudioCapture
from pi.audio.config import AudioCaptureConfig
from pi.audio.errors import AudioCaptureError
from pi.audio.sounddevice_backend import SoundDeviceBackend
from pi.communication import ClientSettings, HttpInterpretationClient
from pi.input.push_to_talk_button import PushToTalkButton
from pi.push_to_talk.controller import (
    DEFAULT_MAX_DURATION_SECONDS,
    PushToTalkController,
)
from pi.push_to_talk.result import AudioCaptureResult
from pi.push_to_talk.sender import RecordingSender
from shared.communication import TransportEnvelope


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
    parser.add_argument(
        "--send-to-pc",
        action="store_true",
        help="send each recording to the PC (VOICESTOCK_PC_URL) and print the answer",
    )
    parser.add_argument(
        "--delete-after-send",
        action="store_true",
        help="delete each WAV once it was sent; requires --send-to-pc",
    )
    args = parser.parse_args(argv)
    if args.delete_after_send and not args.send_to_pc:
        parser.error("--delete-after-send requires --send-to-pc")

    config = AudioCaptureConfig(
        input_device=args.input_device,
        output_directory=args.output_directory,
    )
    capture = AudioCapture(config, SoundDeviceBackend(config.input_device))
    with ExitStack() as resources:
        on_capture_completed: Callable[[AudioCaptureResult], None] = _print_result
        if args.send_to_pc:
            client = resources.enter_context(
                HttpInterpretationClient(ClientSettings.from_environment())
            )
            on_capture_completed = RecordingSender(
                client,
                on_sent=_print_sent_result,
                delete_after_send=args.delete_after_send,
            )
        controller = PushToTalkController(
            capture,
            on_capture_completed=on_capture_completed,
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


def _print_sent_result(result: AudioCaptureResult, envelope: TransportEnvelope) -> None:
    _print_result(result)
    print("PC answer:", flush=True)
    print(envelope.model_dump_json(indent=2), flush=True)


def _print_error(error: AudioCaptureError) -> None:
    print(f"Capture error: {error}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())

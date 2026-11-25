"""One Raspberry Pi process for capture, the PC client, the cycle and the web UI.

The standalone capture, client and web commands stay available for diagnosis.
This module is the composition that shares a single pending-operation flow.
"""

import argparse
import sqlite3
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from pi.audio.capture import AudioCapture
from pi.audio.config import AudioCaptureConfig
from pi.audio.sounddevice_backend import SoundDeviceBackend
from pi.catalog.access import (
    CatalogNotInitializedError,
    OpeningProductResolver,
    OpeningSnapshotReader,
    require_initialized_catalog,
)
from pi.catalog.snapshot import CatalogSnapshotReader
from pi.communication import (
    AudioInterpretationClient,
    ClientSettings,
    HttpInterpretationClient,
)
from pi.operation_contract import OperationValidator
from pi.pending_operation import PendingOperationFlow
from pi.pending_operation.executor import OperationExecutor
from pi.push_to_talk import (
    DEFAULT_MAX_DURATION_SECONDS,
    PushToTalkController,
)
from pi.storage import VolatileDatabasePathError, default_database_path
from pi.web.app import create_app
from pi.web.server import ServerRunner, run_server
from pi.web.settings import WebServerSettings


class _Closeable(Protocol):
    """Resource the runtime stops on the way out."""

    def close(self) -> None:
        """Release the resource. A second call is not required to be safe."""


ButtonFactory = Callable[[PushToTalkController], _Closeable]


class PiRuntime:
    """Shared flow, push-to-talk and web server for one process."""

    def __init__(
        self,
        flow: PendingOperationFlow,
        controller: PushToTalkController,
        button: _Closeable,
        client: AudioInterpretationClient,
        web_settings: WebServerSettings,
        catalog_port: CatalogSnapshotReader | None = None,
    ) -> None:
        self.flow = flow
        self.controller = controller
        self._button = button
        self._client = client
        self.web_settings = web_settings
        self._catalog = catalog_port
        self._closed = False

    def serve(self, runner: ServerRunner | None = None) -> None:
        """Start capture and serve the operator UI until the server returns."""
        self.controller.start()
        app = create_app(
            query_port=self.flow.query_port,
            resolution_port=self.flow.resolution_port,
            status_port=self.flow,
            catalog_port=self._catalog,
        )
        try:
            run_server(self.web_settings, app=app, runner=runner)
        finally:
            self.close()

    def close(self) -> None:
        """Release the button, the capture worker, the cycle and the PC client."""
        if self._closed:
            return
        self._closed = True
        self._button.close()
        self.controller.close()
        self.flow.close()
        closer = getattr(self._client, "close", None)
        if callable(closer):
            closer()


def build_runtime(
    *,
    client: AudioInterpretationClient,
    validator: OperationValidator,
    capture: AudioCapture,
    button_factory: ButtonFactory,
    web_settings: WebServerSettings | None = None,
    max_duration: float = DEFAULT_MAX_DURATION_SECONDS,
    delete_after_send: bool = True,
    executor: OperationExecutor | None = None,
    catalog_port: CatalogSnapshotReader | None = None,
) -> PiRuntime:
    """Wire one flow into push-to-talk and the button factory.

    ``button_factory`` receives the controller so press and release notify the
    same object that reports captures to the flow.
    """
    flow = PendingOperationFlow(
        client,
        validator,
        executor,
        delete_after_send=delete_after_send,
    )
    controller = PushToTalkController(
        capture,
        on_capture_completed=flow.on_capture_completed,
        on_capture_error=flow.on_capture_error,
        max_duration=max_duration,
        can_start_capture=flow.try_begin_recording,
    )
    return PiRuntime(
        flow,
        controller,
        button_factory(controller),
        client,
        web_settings
        if web_settings is not None
        else WebServerSettings.from_environment(),
        catalog_port,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the integrated Raspberry Pi process until the web server stops."""
    args = _parse_args(argv)
    try:
        database = require_initialized_catalog(default_database_path())
    except (
        CatalogNotInitializedError,
        VolatileDatabasePathError,
        sqlite3.Error,
    ) as error:
        print(f"voicestock-pi: {error}", file=sys.stderr)
        return 1
    config = AudioCaptureConfig(
        input_device=args.input_device,
        output_directory=args.output_directory,
    )
    settings = WebServerSettings.from_environment()
    client = HttpInterpretationClient(ClientSettings.from_environment())
    try:
        runtime = build_runtime(
            client=client,
            validator=OperationValidator(OpeningProductResolver(database)),
            catalog_port=OpeningSnapshotReader(database),
            capture=AudioCapture(config, SoundDeviceBackend(config.input_device)),
            button_factory=lambda controller: _physical_button(
                args.pin,
                args.bounce_time,
                controller,
            ),
            web_settings=settings,
            max_duration=args.max_duration,
            delete_after_send=not args.keep_recordings,
        )
        print(f"Web UI: http://{settings.host}:{settings.port}/", flush=True)
        print("VoiceStock is listening. Press Ctrl+C to quit.", flush=True)
        runtime.serve()
    except KeyboardInterrupt:
        print(file=sys.stderr)
    finally:
        client.close()
    return 0


def _physical_button(
    pin: int,
    bounce_time: float,
    controller: PushToTalkController,
) -> _Closeable:
    from pi.input.push_to_talk_button import PushToTalkButton

    return PushToTalkButton(
        pin,
        bounce_time,
        on_pressed=controller.notify_pressed,
        on_released=controller.notify_released,
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="VoiceStock on the Raspberry Pi: button, PC client and web UI",
    )
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
        "--keep-recordings",
        action="store_true",
        help="keep each WAV after it is sent to the PC",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())

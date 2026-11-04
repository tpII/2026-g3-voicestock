"""Send each finished push-to-talk recording to the PC."""

from collections.abc import Callable

from pi.communication import AudioInterpretationClient
from pi.push_to_talk.result import AudioCaptureResult
from shared.communication import TransportEnvelope

SentRecordingHandler = Callable[[AudioCaptureResult, TransportEnvelope], None]


class RecordingSender:
    """Capture consumer that sends the recording's WAV with an audio client.

    Use it as ``on_capture_completed`` of ``PushToTalkController``. It makes
    one send per recording and hands the resulting ``TransportEnvelope`` to
    ``on_sent``, success or error alike, so a communication failure never
    stops push-to-talk. It does not retry and does not read the payload.

    The sender owns the file after the controller delivers it.
    ``delete_after_send`` decides whether the WAV is deleted once the send
    finished, whatever its result, or kept on disk.
    """

    def __init__(
        self,
        client: AudioInterpretationClient,
        on_sent: SentRecordingHandler,
        *,
        delete_after_send: bool,
    ) -> None:
        self._client = client
        self._on_sent = on_sent
        self._delete_after_send = delete_after_send

    def __call__(self, result: AudioCaptureResult) -> None:
        try:
            envelope = self._client.interpret_audio(result.artifact.path)
            self._on_sent(result, envelope)
        finally:
            if self._delete_after_send:
                result.artifact.cleanup()

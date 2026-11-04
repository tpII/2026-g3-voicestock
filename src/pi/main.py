"""Raspberry Pi command that sends one text or WAV to the PC and prints the envelope.

It lets anyone reproduce the Raspberry Pi -> PC roundtrip from a terminal
until the rest of the Raspberry Pi system drives the client itself.
"""

import sys
from pathlib import Path

from pi.communication import ClientSettings, HttpInterpretationClient

USAGE = (
    'usage: voicestock-pi-client "texto reconocido"\n'
    "       voicestock-pi-client --audio grabacion.wav"
)


def main(argv: list[str] | None = None) -> int:
    """Send the given text or WAV file and print the TransportEnvelope as JSON.

    Returns 0 when the envelope is a success, 1 when it is an error and 2 for
    wrong arguments.
    """
    args = sys.argv[1:] if argv is None else argv
    if not args or (args[0] == "--audio" and len(args) != 2):
        print(USAGE, file=sys.stderr)
        return 2

    with HttpInterpretationClient(ClientSettings.from_environment()) as client:
        if args[0] == "--audio":
            envelope = client.interpret_audio(Path(args[1]))
        else:
            envelope = client.interpret(" ".join(args))

    print(envelope.model_dump_json(indent=2))
    return 0 if envelope.status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())

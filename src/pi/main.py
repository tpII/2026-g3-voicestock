"""Raspberry Pi command that sends one text to the PC and prints the envelope.

It lets anyone reproduce the Raspberry Pi -> PC roundtrip from a terminal
until SpeechToText and PendingOperationFlow drive the client themselves.
"""

import sys

from pi.communication import ClientSettings, HttpInterpretationClient


def main(argv: list[str] | None = None) -> int:
    """Send the given text and print the TransportEnvelope as JSON.

    Returns 0 when the envelope is a success and 1 when it is an error.
    """
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print('usage: voicestock-pi-client "texto reconocido"', file=sys.stderr)
        return 2

    with HttpInterpretationClient(ClientSettings.from_environment()) as client:
        envelope = client.interpret(" ".join(args))

    print(envelope.model_dump_json(indent=2))
    return 0 if envelope.status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())

# Evidence

No evidence has been filed. This directory explains where evidence goes
when a run happens.

## What may be committed

- Redacted command transcripts (`.txt` or `.log`) small enough to review.
- SHA-256 manifests.
- Photographs that do not show credentials, and only when a case asks for
  a wiring photo. Prefer an external archive even then.

## What stays outside git

- WAV and other audio.
- Video of the operator or the screen.
- Packet captures.
- Untrimmed application logs.
- Any file that contains an API key, a token, or the Wi-Fi passphrase.

The execution record stores the external URI and the SHA-256. The URI must
still be resolvable by the reviewer who moves the case to **CLOSED_PASSED**.

Name external objects with the evidence id from the execution record so the
link is traceable without opening the file.

## Checksums

On the machine that produced the file:

```bash
sha256sum path/to/file
```

Record the hash in the execution table. A later copy that does not match is
a broken reference, not a successful retest.

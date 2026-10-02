"""Published audio file handed back to the caller."""

from pathlib import Path


class AudioArtifact:
    """Identity and filesystem lifecycle of one finished recording.

    The artifact does not describe why the recording stopped. The caller owns
    the file after ``AudioCapture.stop`` returns and decides when to delete it.
    """

    def __init__(self, artifact_id: str, path: Path) -> None:
        self._id = artifact_id
        self._path = path

    @property
    def id(self) -> str:
        """Stable identifier. It is not derived from ``path`` at read time."""
        return self._id

    @property
    def path(self) -> Path:
        """Filesystem path of the published WAV."""
        return self._path

    def cleanup(self) -> None:
        """Delete the published file if it is still present."""
        self._path.unlink(missing_ok=True)

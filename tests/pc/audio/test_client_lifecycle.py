"""Groq client ownership follows the ASGI lifespan. No live API call is made."""

import json
from pathlib import Path

import httpx
import pytest

from pc.audio.factory import audio_session_for
from pc.audio.settings import AudioPipelineSettings
from pc.communication.audio import ReceivedAudio
from pc.main import create_pc_app, default_registry, describe_received_audio

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class TrackingClient(httpx.Client):
    """Counts how many times the shared client is closed."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1
        super().close()


def _audio() -> ReceivedAudio:
    return ReceivedAudio(
        wav=b"RIFF",
        duration_seconds=0.1,
        sample_rate_hz=16000,
        channels=1,
        sample_width_bytes=2,
    )


def _catalog(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "name": "Arroz",
                    "brand": "Marolio",
                    "variant": None,
                    "presentation": "1 kg",
                }
            ]
        ),
        encoding="utf-8",
    )


async def test_stub_session_does_not_open_a_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("stub mode created a Groq resource")

    monkeypatch.setattr("pc.audio.factory.httpx.Client", forbidden)
    monkeypatch.setattr("pc.audio.factory.GroqWhisperTranscriber", forbidden)
    monkeypatch.setattr("pc.audio.factory.GroqChatPoster", forbidden)
    session = audio_session_for(AudioPipelineSettings(), describe_received_audio)
    app = create_pc_app(
        default_registry(),
        "stub",
        session.handle,
        session.lifespan,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.post("/api/v1/interpret", json={"text": "hola"})
    assert response.status_code == 200
    assert session.handle(_audio()).status == "success"
    session.close()


async def test_groq_client_is_shared_and_closes_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    created: list[TrackingClient] = []

    def build_client(*args: object, **kwargs: object) -> TrackingClient:
        client = TrackingClient(*args, **kwargs)
        created.append(client)
        return client

    monkeypatch.setattr("pc.audio.factory.httpx.Client", build_client)
    catalog = tmp_path / "catalog.json"
    _catalog(catalog)
    session = audio_session_for(
        AudioPipelineSettings(
            mode="groq",
            catalog_path=catalog,
            api_key="not-a-real-key",
        ),
        describe_received_audio,
    )
    assert created == []
    app = create_pc_app(
        default_registry(),
        "stub",
        session.handle,
        session.lifespan,
    )
    async with app.router.lifespan_context(app):
        assert len(created) == 1
        assert session._transcriber is not None
        assert session._poster is not None
        assert session._transcriber._client is created[0]
        assert session._poster._client is created[0]
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.post("/api/v1/interpret", json={"text": "hola"})
        assert response.status_code == 200
    assert created[0].close_calls == 1
    session.close()
    assert created[0].close_calls == 1

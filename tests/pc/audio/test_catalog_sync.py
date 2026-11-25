"""The PC asks the Raspberry Pi for the catalog before interpreting audio."""

import json

import httpx
import pytest

from pc.audio.catalog import CatalogSnapshotError, parse_catalog_snapshot
from pc.audio.factory import GroqAudioSession
from pc.audio.pi_catalog import PiCatalogSession
from pc.audio.settings import AudioPipelineSettings
from pc.communication.audio import ReceivedAudio
from pc.interpretation.groq import GroqDraftProvider
from pc.interpretation.results import ServiceErrorCode

REVISION = "a" * 64
NEXT = "b" * 64


def _product(
    product_id: str = "gaseosa-coca-cola-zero-1500",
    *,
    name: str = "Gaseosa",
    brand: str | None = "Coca-Cola",
    variant: str | None = "Zero",
    presentation: str | None = "1.5 L",
    aliases: list[str] | None = None,
) -> dict[str, object]:
    return {
        "product_id": product_id,
        "name": name,
        "brand": brand,
        "variant": variant,
        "presentation": presentation,
        "units": ["unit"],
        "aliases": ["Coca Zero de litro y medio"] if aliases is None else aliases,
    }


def _body(revision: str, products: list[dict[str, object]]) -> dict[str, object]:
    return {"version": 1, "revision": revision, "products": products}


def _ok(revision: str, products: list[dict[str, object]]) -> httpx.Response:
    return httpx.Response(
        200,
        json=_body(revision, products),
        headers={"ETag": f'"{revision}"'},
    )


def _audio() -> ReceivedAudio:
    return ReceivedAudio(
        wav=b"RIFF",
        duration_seconds=0.1,
        sample_rate_hz=16000,
        channels=1,
        sample_width_bytes=2,
    )


def _draft() -> dict[str, object]:
    return {
        "operaciones": [
            {
                "operacion": "agregar_stock",
                "producto": {
                    "nombre": "Gaseosa",
                    "marca": "Coca-Cola",
                    "variante": "Zero",
                    "presentacion": "1.5 L",
                },
                "cantidad": 2,
            }
        ]
    }


class _Script:
    def __init__(self, responses: list[httpx.Response | Exception]) -> None:
        self.responses = responses
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _session(script: _Script) -> PiCatalogSession:
    client = httpx.Client(transport=httpx.MockTransport(script))
    return PiCatalogSession("http://192.168.50.1:8000", client)


def test_the_first_request_installs_a_snapshot() -> None:
    script = _Script([_ok(REVISION, [_product()])])
    catalog = _session(script)
    pulled = catalog.pull()
    catalog.accept(pulled)

    assert script.requests[0].headers.get("if-none-match") is None
    assert script.requests[0].url.path == "/api/v1/catalog"
    assert pulled.revision == REVISION
    assert pulled.entries[0].aliases == ("Coca Zero de litro y medio",)
    assert "product_id" not in json.dumps(pulled.entries[0].as_prompt_row())
    catalog.close()


def test_304_reuses_the_installed_snapshot_without_a_body() -> None:
    script = _Script(
        [
            _ok(REVISION, [_product()]),
            httpx.Response(304, headers={"ETag": f'"{REVISION}"'}),
        ]
    )
    catalog = _session(script)
    first = catalog.pull()
    catalog.accept(first)
    second = catalog.pull()

    assert script.requests[1].headers["if-none-match"] == f'"{REVISION}"'
    assert second is first
    catalog.close()


def test_200_replaces_the_snapshot_only_after_accept() -> None:
    script = _Script(
        [
            _ok(REVISION, [_product()]),
            _ok(NEXT, [_product(aliases=["Coca Zero grande"])]),
        ]
    )
    catalog = _session(script)
    first = catalog.pull()
    catalog.accept(first)
    second = catalog.pull()

    assert catalog.current is first
    catalog.accept(second)
    assert catalog.current is second
    assert second.entries[0].aliases == ("Coca Zero grande",)
    catalog.close()


def test_an_invalid_snapshot_does_not_replace_the_previous_one() -> None:
    script = _Script(
        [
            _ok(REVISION, [_product()]),
            _ok(NEXT, [_product(), _product()]),
        ]
    )
    catalog = _session(script)
    first = catalog.pull()
    catalog.accept(first)
    with pytest.raises(Exception, match="duplicated"):
        catalog.pull()
    assert catalog.current is first
    catalog.close()


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(404),
        httpx.Response(500),
        httpx.Response(201, json=_body(REVISION, [_product()])),
        httpx.Response(200, content=b"{", headers={"ETag": f'"{REVISION}"'}),
        httpx.Response(
            200,
            json=_body(REVISION, [_product()]),
            headers={"ETag": f'"{NEXT}"'},
        ),
        httpx.Response(200, json=_body(REVISION, [_product()])),
        httpx.Response(
            200,
            json={"version": 2, "revision": REVISION, "products": [_product()]},
            headers={"ETag": f'"{REVISION}"'},
        ),
    ],
)
def test_bad_catalog_responses_are_rejected(response: httpx.Response) -> None:
    catalog = _session(_Script([response]))
    with pytest.raises(Exception, match="catalog"):
        catalog.pull()
    assert catalog.current is None
    catalog.close()


def test_304_without_a_snapshot_is_rejected() -> None:
    catalog = _session(
        _Script([httpx.Response(304, headers={"ETag": f'"{REVISION}"'})])
    )
    with pytest.raises(Exception, match="304"):
        catalog.pull()
    catalog.close()


def test_304_with_a_different_etag_keeps_the_snapshot() -> None:
    script = _Script(
        [
            _ok(REVISION, [_product()]),
            httpx.Response(304, headers={"ETag": f'"{NEXT}"'}),
        ]
    )
    catalog = _session(script)
    first = catalog.pull()
    catalog.accept(first)
    with pytest.raises(Exception, match="304"):
        catalog.pull()
    assert catalog.current is first
    catalog.close()


def test_transport_failures_do_not_install_a_snapshot() -> None:
    for error in (
        httpx.ConnectError("down"),
        httpx.ConnectTimeout("connect"),
        httpx.ReadTimeout("read"),
    ):
        catalog = _session(_Script([error]))
        with pytest.raises(Exception, match="catalog"):
            catalog.pull()
        assert catalog.current is None
        catalog.close()


def test_unreachable_products_are_rejected() -> None:
    products = [
        _product(
            product_id="arroz",
            name="Arroz",
            brand=None,
            variant=None,
            presentation=None,
            aliases=[],
        ),
        _product(
            product_id="arroz-gallo",
            name="Arroz",
            brand="Gallo",
            variant=None,
            presentation="1 kg",
            aliases=[],
        ),
    ]
    with pytest.raises(CatalogSnapshotError, match="not identifiable"):
        parse_catalog_snapshot(_body(REVISION, products), f'"{REVISION}"')


class _Transcriber:
    def __init__(self, **kwargs: object) -> None:
        self.calls = 0
        self._client = kwargs["client"]

    def transcribe(self, wav: bytes) -> str:
        del wav
        self.calls += 1
        return "agregá dos coca zero de litro y medio"


class _Poster:
    def __init__(self, **kwargs: object) -> None:
        self._client = kwargs["client"]

    def __call__(self, payload: dict[str, object]) -> dict[str, object]:
        del payload
        return {"choices": [{"message": {"content": json.dumps(_draft())}}]}


def _audio_session(
    monkeypatch: pytest.MonkeyPatch, script: _Script
) -> tuple[GroqAudioSession, _Transcriber]:
    transcribers: list[_Transcriber] = []
    client_cls = httpx.Client

    def build_client(*args: object, **kwargs: object) -> httpx.Client:
        del args
        if "timeout" in kwargs:
            return client_cls(transport=httpx.MockTransport(script), timeout=5.0)
        return client_cls(
            transport=httpx.MockTransport(lambda request: httpx.Response(500))
        )

    def build_transcriber(**kwargs: object) -> _Transcriber:
        transcriber = _Transcriber(**kwargs)
        transcribers.append(transcriber)
        return transcriber

    monkeypatch.setattr("pc.audio.factory.httpx.Client", build_client)
    monkeypatch.setattr("pc.audio.factory.GroqWhisperTranscriber", build_transcriber)
    monkeypatch.setattr("pc.audio.factory.GroqChatPoster", _Poster)
    session = GroqAudioSession(
        AudioPipelineSettings(
            mode="groq", api_key="not-a-real-key", pi_base_url="http://pi.test"
        )
    )
    session.start()
    return session, transcribers[0]


def test_interpretation_uses_the_downloaded_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[object] = []
    real = GroqDraftProvider

    class Counting(real):
        def __init__(self, **kwargs: object) -> None:
            created.append(kwargs["catalog"])
            super().__init__(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr("pc.audio.factory.GroqDraftProvider", Counting)
    script = _Script(
        [
            _ok(REVISION, [_product()]),
            httpx.Response(304, headers={"ETag": f'"{REVISION}"'}),
            _ok(
                NEXT,
                [
                    _product(
                        product_id="gaseosa-coca-cola-original-1500",
                        variant="Original",
                        aliases=["Coca de litro y medio"],
                    )
                ],
            ),
        ]
    )
    session, transcriber = _audio_session(monkeypatch, script)
    first = session.handle(_audio())
    second = session.handle(_audio())

    assert first.status == "success"
    assert first.payload["operations"][0]["product"]["name"] == "Gaseosa"
    assert first.payload["operations"][0]["product"]["variant"] == "Zero"
    assert "product_id" not in json.dumps(first.payload)
    assert "Coca Zero de litro y medio" in json.dumps(created[0])
    assert len(created) == 1
    assert second.status == "success"
    assert len(created) == 1
    assert script.requests[0].headers.get("if-none-match") is None
    assert script.requests[1].headers["if-none-match"] == f'"{REVISION}"'

    updated = _draft()
    product = updated["operaciones"][0]["producto"]  # type: ignore[index]
    product["variante"] = "Original"  # type: ignore[index]

    def original_poster(self: _Poster, payload: dict[str, object]) -> dict[str, object]:
        del self, payload
        return {"choices": [{"message": {"content": json.dumps(updated)}}]}

    monkeypatch.setattr(_Poster, "__call__", original_poster)
    third = session.handle(_audio())
    assert third.status == "success"
    assert third.payload["operations"][0]["product"]["variant"] == "Original"
    assert len(created) == 2
    assert "Coca de litro y medio" in json.dumps(created[1])
    assert transcriber.calls == 3
    session.close()


def test_catalog_failure_skips_transcription_and_the_next_request_recovers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = _Script([httpx.ConnectError("down"), _ok(REVISION, [_product()])])
    session, transcriber = _audio_session(monkeypatch, script)
    failed = session.handle(_audio())
    assert failed.status == "error"
    assert failed.error is not None
    assert failed.error.code is ServiceErrorCode.CATALOG_UNAVAILABLE
    assert transcriber.calls == 0
    recovered = session.handle(_audio())
    assert recovered.status == "success"
    assert transcriber.calls == 1
    session.close()


def test_stub_settings_do_not_require_the_pi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICESTOCK_AUDIO_PIPELINE", "stub")
    monkeypatch.setenv("VOICESTOCK_PI_URL", "not a url")
    settings = AudioPipelineSettings.from_environment()
    assert settings.mode == "stub"
    assert settings.pi_base_url == "not a url"


def test_groq_settings_require_an_absolute_pi_url() -> None:
    with pytest.raises(ValueError, match="VOICESTOCK_PI_URL"):
        AudioPipelineSettings(mode="groq", api_key="k", pi_base_url="192.168.50.1:8000")

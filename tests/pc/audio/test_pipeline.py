"""Audio pipeline composition with stand-ins for Groq."""

import io
import wave

import httpx
import pytest

from pc.audio.catalog import CatalogEntry
from pc.audio.pipeline import build_pipeline
from pc.communication.audio import ReceivedAudio
from pc.interpretation.providers import ProviderError
from pc.interpretation.results import ServiceErrorCode
from pc.main import create_pc_app, default_registry
from pi.operation_contract import (
    CatalogProduct,
    InMemoryProductResolver,
    OperationValidator,
)
from pi.pending_operation.response import OutcomeKind, PcResponseInterpreter
from shared.communication import TransportEnvelope

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


CATALOG = (
    CatalogEntry(name="Arroz", brand="Marolio", presentation="1 kg"),
    CatalogEntry(name="Arroz", brand="Marolio", presentation="500 g"),
)
PRODUCTS = (
    CatalogProduct(
        product_id="arroz-marolio-1kg",
        name="Arroz",
        brand="Marolio",
        presentation="1 kg",
    ),
    CatalogProduct(
        product_id="arroz-marolio-500g",
        name="Arroz",
        brand="Marolio",
        presentation="500 g",
    ),
)


class _Provider:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def interpret(self, text: str) -> object:
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


def _audio() -> ReceivedAudio:
    return ReceivedAudio(
        wav=_wav_bytes(),
        duration_seconds=0.1,
        sample_rate_hz=16000,
        channels=1,
        sample_width_bytes=2,
    )


def _wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x00\x00" * 1600)
    return buffer.getvalue()


def _product(presentation: str | None) -> dict[str, str | None]:
    return {
        "nombre": "Arroz",
        "marca": "Marolio",
        "variante": None,
        "presentacion": presentation,
    }


def _draft(presentation: str | None, quantity: int = 2) -> dict[str, object]:
    return {
        "operaciones": [
            {
                "operacion": "agregar_stock",
                "producto": _product(presentation),
                "cantidad": quantity,
            }
        ]
    }


def _pipeline(text: str, payload: object):
    return build_pipeline(lambda wav: text, _Provider(payload), CATALOG)


def test_unambiguous_command_keeps_recognized_text_and_attributes() -> None:
    text = "agregá dos paquetes de arroz marolio de un kilo"
    result = _pipeline(text, _draft("1 kg")).handle(_audio())
    assert result.status == "success"
    assert result.payload["recognized_text"] == text
    operation = result.payload["operations"][0]
    assert operation["product"] == {
        "name": "Arroz",
        "brand": "Marolio",
        "variant": None,
        "presentation": "1 kg",
    }
    assert "product_id" not in result.model_dump_json()


def test_ambiguous_rice_command_is_rejected() -> None:
    result = _pipeline("agregá dos paquetes de arroz", _draft(None)).handle(_audio())
    assert result.error is not None
    assert result.error.code is ServiceErrorCode.AMBIGUOUS_PRODUCT
    assert result.payload is None


def test_unknown_product_is_rejected() -> None:
    draft = _draft("1 kg")
    draft["operaciones"][0]["producto"] = _product("1 kg") | {"nombre": "Fideos"}
    result = _pipeline("agregá fideos", draft).handle(_audio())
    assert result.error is not None
    assert result.error.code is ServiceErrorCode.UNKNOWN_PRODUCT


def test_extra_operation_is_not_discarded() -> None:
    draft = _draft("1 kg")
    draft["operaciones"].append(draft["operaciones"][0])
    result = _pipeline("dos operaciones", draft).handle(_audio())
    assert result.error is not None
    assert result.error.code is ServiceErrorCode.UNSUPPORTED_COMMAND
    assert "got 2" in (result.error.detail or "")


def test_mapper_failure_stays_a_service_error() -> None:
    draft = _draft("1 kg")
    del draft["operaciones"][0]["producto"]["presentacion"]
    result = _pipeline("incompleto", draft).handle(_audio())
    assert result.error is not None
    assert result.error.code is ServiceErrorCode.CONTRACT_MAPPING_FAILURE


def test_empty_transcription_is_not_a_contract() -> None:
    from pc.speech_to_text import TranscriptionError, TranscriptionFailure

    def empty(wav: bytes) -> str:
        raise TranscriptionError(TranscriptionFailure.EMPTY, "transcription is blank")

    result = build_pipeline(empty, _Provider(_draft("1 kg")), CATALOG).handle(_audio())
    assert result.error is not None
    assert result.error.code is ServiceErrorCode.EMPTY_TRANSCRIPTION


def test_transcription_timeout_and_failure() -> None:
    from pc.speech_to_text import TranscriptionError, TranscriptionFailure

    def timeout(wav: bytes) -> str:
        raise TranscriptionError(TranscriptionFailure.TIMEOUT, "timed out")

    def failed(wav: bytes) -> str:
        raise TranscriptionError(TranscriptionFailure.FAILED, "HTTP 503")

    timed = build_pipeline(timeout, _Provider(_draft("1 kg")), CATALOG).handle(_audio())
    broken = build_pipeline(failed, _Provider(_draft("1 kg")), CATALOG).handle(_audio())
    assert timed.error is not None
    assert broken.error is not None
    assert timed.error.code is ServiceErrorCode.TRANSCRIPTION_TIMEOUT
    assert broken.error.code is ServiceErrorCode.TRANSCRIPTION_FAILURE


def test_unexpected_mapping_error_hides_the_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(draft: object) -> object:
        raise RuntimeError("secret-mapper-body")

    monkeypatch.setattr("pc.audio.pipeline.map_draft", explode)
    result = _pipeline("agregá arroz", _draft("1 kg")).handle(_audio())
    assert result.error is not None
    assert result.error.code is ServiceErrorCode.CONTRACT_MAPPING_FAILURE
    assert result.error.detail == "contract mapping failed"
    assert "secret-mapper-body" not in (result.error.detail or "")


def test_unexpected_provider_error_then_a_valid_contract() -> None:
    class Once:
        def __init__(self) -> None:
            self.calls = 0

        def interpret(self, text: str) -> object:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("secret-provider-body")
            return _draft("1 kg")

    text = "agregá dos paquetes de arroz marolio de un kilo"
    pipeline = build_pipeline(lambda wav: text, Once(), CATALOG)
    failed = pipeline.handle(_audio())
    assert failed.error is not None
    assert failed.error.code is ServiceErrorCode.PROVIDER_FAILURE
    assert failed.error.detail == "the provider failed unexpectedly"
    succeeded = pipeline.handle(_audio())
    assert succeeded.payload is not None
    assert succeeded.payload["recognized_text"] == text
    assert "secret-provider-body" not in succeeded.model_dump_json()


def test_provider_failure_does_not_create_a_contract() -> None:
    result = _pipeline(
        "texto", ProviderError("interpretation request timed out")
    ).handle(_audio())
    assert result.error is not None
    assert result.error.code is ServiceErrorCode.PROVIDER_FAILURE
    assert result.payload is None


async def test_http_contract_is_accepted_by_the_raspberry_validator() -> None:
    text = "agregá dos paquetes de arroz marolio de un kilo"
    pipeline = _pipeline(text, _draft("1 kg"))
    app = create_pc_app(default_registry(), "stub", audio_handler=pipeline.handle)
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/api/v1/interpret-audio",
            content=_wav_bytes(),
            headers={"content-type": "audio/wav"},
        )

    assert response.status_code == 200
    envelope = TransportEnvelope.model_validate(response.json())
    interpreter = PcResponseInterpreter(
        OperationValidator(InMemoryProductResolver(PRODUCTS))
    )
    outcome = interpreter.interpret(envelope)
    assert outcome.kind is OutcomeKind.ACCEPTED
    assert outcome.recognized_text == text
    assert outcome.validated_operation is not None
    assert outcome.validated_operation.product_id == "arroz-marolio-1kg"
    assert outcome.validated_operation.quantity == 2
    assert "super-secret" not in response.text

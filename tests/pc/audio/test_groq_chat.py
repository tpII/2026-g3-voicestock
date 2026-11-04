"""HTTP wrapper for the Groq chat call. No live API call is made."""

import httpx
import pytest

from pc.audio.groq_chat import GroqChatPoster
from pc.interpretation.providers import ProviderError

SECRET = "super-secret-groq-key"


def test_http_failure_hides_the_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == f"Bearer {SECRET}"
        return httpx.Response(500, text=SECRET)

    poster = GroqChatPoster(
        api_key=SECRET,
        timeout_seconds=5,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ProviderError) as caught:
        poster({"model": "openai/gpt-oss-20b"})
    assert SECRET not in str(caught.value)
    assert "HTTP 500" in str(caught.value)


def test_malformed_json_hides_the_body(caplog: pytest.LogCaptureFixture) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=f"not-json {SECRET}")

    poster = GroqChatPoster(
        api_key=SECRET,
        timeout_seconds=5,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with caplog.at_level("DEBUG"), pytest.raises(ProviderError, match="not JSON"):
        poster({"model": "openai/gpt-oss-20b"})
    assert SECRET not in caplog.text


def test_unexpected_client_error_hides_the_secret(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class ExplodingClient:
        def post(self, *args: object, **kwargs: object) -> object:
            raise RuntimeError(f"Bearer {SECRET} raw-audio")

    poster = GroqChatPoster(
        api_key=SECRET,
        timeout_seconds=5,
        client=ExplodingClient(),  # type: ignore[arg-type]
    )
    with caplog.at_level("DEBUG"), pytest.raises(ProviderError, match="failed"):
        poster({"model": "openai/gpt-oss-20b"})
    assert SECRET not in caplog.text
    assert "raw-audio" not in caplog.text

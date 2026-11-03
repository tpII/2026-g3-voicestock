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

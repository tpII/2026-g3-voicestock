"""HTTP call used by the Groq draft provider.

Failures become ``ProviderError`` messages that do not include the API key
or the response body.
"""

import logging
from typing import Any

import httpx

from pc.interpretation.providers import ProviderError

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqChatPoster:
    """POST one chat completion and return the decoded JSON object."""

    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float,
        client: httpx.Client,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Groq API key must not be blank")
        if timeout_seconds <= 0:
            raise ValueError("LLM timeout must be positive")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._client = client

    def __call__(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(
                GROQ_CHAT_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
        except httpx.TimeoutException:
            logger.info("interpretation request timed out")
            raise ProviderError("interpretation request timed out") from None
        except httpx.HTTPStatusError as error:
            logger.info("interpretation request failed")
            raise ProviderError(
                f"interpretation request failed with HTTP {error.response.status_code}"
            ) from None
        except httpx.HTTPError:
            logger.info("interpretation request failed")
            raise ProviderError("interpretation request failed") from None
        except ValueError:
            logger.info("interpretation response was not accepted")
            raise ProviderError("interpretation response is not JSON") from None
        except Exception:
            logger.info("interpretation request failed unexpectedly")
            raise ProviderError("interpretation request failed") from None
        if not isinstance(body, dict):
            raise ProviderError("interpretation response is not an object")
        return body

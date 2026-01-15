"""Adapter per interazione con ElevenLabs API.

Dewey: Conseguenze pratiche - gestione robusta HTTP e streaming.
Separazione netta: questo modulo si occupa SOLO di HTTP/IO.
"""

import logging
import os
import types
from collections.abc import Iterator
from typing import NoReturn, Self

import httpx

from eleven_tts_cli.core.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    VoiceNotFoundError,
)
from eleven_tts_cli.core.models import Voice

logger = logging.getLogger(__name__)


class ElevenLabsClient:
    """Client per interazione con ElevenLabs API.

    Platone: Trasparenza - ogni metodo ha responsabilità chiara.
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str | None = None):
        """Inizializza client con API key.

        Args:
            api_key: API key ElevenLabs. Se None, legge da env var ELEVENLABS_API_KEY.

        Raises:
            AuthenticationError: Se API key non fornita e non trovata in env.
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "ELEVENLABS_API_KEY not found. "
                "Set environment variable or pass api_key parameter."
            )

        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "xi-api-key": self.api_key,
            },
            timeout=httpx.Timeout(30.0, connect=10.0, read=120.0),
        )

    def get_voices(self) -> list[Voice]:
        """Recupera lista delle voci disponibili.

        Returns:
            Lista di oggetti Voice.

        Raises:
            AuthenticationError: Se API key non valida.
            NetworkError: Se errore di rete.
            APIError: Per altri errori API.
        """
        logger.info("Fetching voices from ElevenLabs API")

        try:
            response = self.client.get("/voices", headers={"Accept": "application/json"})
            response.raise_for_status()

            data = response.json()
            voices = [
                Voice(
                    voice_id=v["voice_id"],
                    name=v["name"],
                    category=v.get("category"),
                    labels=v.get("labels"),
                )
                for v in data.get("voices", [])
            ]

            logger.info(f"Retrieved {len(voices)} voices")
            return voices

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise NetworkError(f"Network error while fetching voices: {e}") from e

    def text_to_speech_stream(
        self,
        text: str,
        voice_id: str,
        model_id: str = "eleven_monolingual_v1",
    ) -> Iterator[bytes]:
        """Converte testo in audio con streaming.

        Args:
            text: Testo da convertire.
            voice_id: ID della voce da utilizzare.
            model_id: Modello TTS da usare (default: eleven_monolingual_v1).

        Yields:
            Chunk di audio in formato bytes.

        Raises:
            VoiceNotFoundError: Se voice_id non esiste.
            AuthenticationError: Se API key non valida.
            RateLimitError: Se rate limit superato.
            NetworkError: Se errore di rete.
            APIError: Per altri errori API.
        """
        logger.info(f"Starting TTS for voice_id={voice_id}, text length={len(text)}")

        endpoint = f"/text-to-speech/{voice_id}"
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        try:
            with self.client.stream(
                "POST",
                endpoint,
                json=payload,
                headers={"Accept": "audio/mpeg"},
            ) as response:
                response.raise_for_status()

                total_bytes = 0
                for chunk in response.iter_bytes(chunk_size=8192):
                    if chunk:
                        total_bytes += len(chunk)
                        yield chunk

                logger.info(f"TTS streaming completed: {total_bytes} bytes")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise VoiceNotFoundError(voice_id) from e
            self._handle_http_error(e)
        except httpx.RequestError as e:
            logger.error(f"Network error during TTS: {e}")
            raise NetworkError(f"Network error during text-to-speech: {e}") from e

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> NoReturn:
        """Gestisce errori HTTP mappandoli a custom exceptions.

        Args:
            error: Errore HTTP da httpx.

        Raises:
            AuthenticationError: Per 401.
            RateLimitError: Per 429.
            APIError: Per altri status code.
        """
        status_code = error.response.status_code

        if status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif status_code == 429:
            raise RateLimitError()
        else:
            logger.error(f"API error {status_code}: {error.response.text}")
            raise APIError(f"API error ({status_code}): {error.response.text}")

    def close(self) -> None:
        """Chiude connessione HTTP client."""
        self.client.close()

    def __enter__(self) -> Self:
        """Context manager support."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Context manager cleanup."""
        self.close()

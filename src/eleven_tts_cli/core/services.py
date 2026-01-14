"""Business logic per TTS operations.

Platone: Valori = Semplicità d'uso + Robustezza + Manutenibilità.
Separazione netta: logica pura, nessun I/O diretto qui (delegato ad adapter).
"""

import logging
from pathlib import Path

from eleven_tts_cli.adapters.elevenlabs_api import ElevenLabsClient
from eleven_tts_cli.core.errors import FileSystemError
from eleven_tts_cli.core.models import TTSRequest, Voice

logger = logging.getLogger(__name__)


class TTSService:
    """Service per operazioni text-to-speech.

    Aristotele: Definizione chiara - questo service orchestra le operazioni
    ma non gestisce né HTTP né interazione utente.
    """

    def __init__(self, api_client: ElevenLabsClient):
        """Inizializza service con client API.

        Args:
            api_client: Client per comunicazione con ElevenLabs API.
        """
        self.api_client = api_client

    def list_voices(self) -> list[Voice]:
        """Recupera lista delle voci disponibili.

        Returns:
            Lista di voci ordinate alfabeticamente per nome.

        Raises:
            AuthenticationError: Se API key non valida.
            NetworkError: Se errore di rete.
            APIError: Per altri errori API.
        """
        logger.info("Listing available voices")
        voices = self.api_client.get_voices()

        # Ordina alfabeticamente per UX migliore
        voices_sorted = sorted(voices, key=lambda v: v.name.lower())

        return voices_sorted

    def generate_audio(self, request: TTSRequest) -> None:
        """Genera audio da testo e salva su file.

        Args:
            request: Richiesta TTS con testo, voice_id e output_path.

        Raises:
            VoiceNotFoundError: Se voice_id non esiste.
            FileSystemError: Se errore scrittura file.
            NetworkError: Se errore di rete.
            APIError: Per altri errori API.
        """
        logger.info(
            f"Generating audio: voice={request.voice_id}, "
            f"text_length={len(request.text)}, output={request.output_path}"
        )

        output_path = Path(request.output_path)

        # Verifica directory esistente
        if not output_path.parent.exists():
            raise FileSystemError(f"Output directory does not exist: {output_path.parent}")

        # Verifica permessi scrittura (approssimativo)
        if output_path.exists() and not output_path.is_file():
            raise FileSystemError(f"Output path exists but is not a file: {output_path}")

        try:
            # Streaming audio da API e scrittura incrementale
            with open(output_path, "wb") as audio_file:
                bytes_written = 0

                for chunk in self.api_client.text_to_speech_stream(
                    text=request.text,
                    voice_id=request.voice_id,
                ):
                    audio_file.write(chunk)
                    bytes_written += len(chunk)

                logger.info(f"Audio saved: {output_path} ({bytes_written} bytes)")

        except OSError as e:
            logger.error(f"File system error: {e}")
            raise FileSystemError(f"Error writing audio file: {e}") from e

    def search_voices(self, query: str, voices: list[Voice]) -> list[Voice]:
        """Filtra voci per nome o ID usando query testuale.

        Dewey: Conseguenza pratica - UX migliore con ricerca testuale.

        Args:
            query: Stringa di ricerca (case-insensitive).
            voices: Lista di voci da filtrare.

        Returns:
            Lista di voci che matchano la query.
        """
        query_lower = query.lower().strip()

        if not query_lower:
            return voices

        return [
            v for v in voices if query_lower in v.name.lower() or query_lower in v.voice_id.lower()
        ]

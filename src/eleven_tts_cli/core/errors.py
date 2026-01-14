"""Custom exceptions for ElevenLabs TTS CLI.

Aristotele: Ogni errore ha un significato chiaro e specifico.
Platone: Robustezza attraverso gestione errori esplicita.
"""


class ElevenLabsCLIError(Exception):
    """Base exception per tutti gli errori dell'applicazione."""
    pass


class APIError(ElevenLabsCLIError):
    """Errore generico durante chiamata API ElevenLabs."""
    pass


class AuthenticationError(APIError):
    """API key mancante o non valida."""
    pass


class RateLimitError(APIError):
    """Rate limit API superato."""

    def __init__(self, message: str = "API rate limit exceeded. Please try again later."):
        super().__init__(message)


class NetworkError(APIError):
    """Errore di rete durante chiamata API."""
    pass


class VoiceNotFoundError(APIError):
    """Voice ID richiesto non esiste."""

    def __init__(self, voice_id: str):
        super().__init__(f"Voice with ID '{voice_id}' not found")
        self.voice_id = voice_id


class ValidationError(ElevenLabsCLIError):
    """Errore validazione input utente."""
    pass


class FileSystemError(ElevenLabsCLIError):
    """Errore durante operazioni su file system."""
    pass

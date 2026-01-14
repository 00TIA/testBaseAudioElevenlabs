"""Domain models for ElevenLabs TTS CLI.

Aristotele: Definizioni chiare delle entità del dominio.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Voice:
    """Rappresenta una voce ElevenLabs disponibile.

    Attributes:
        voice_id: Identificatore univoco della voce (es. "21m00Tcm4TlvDq8ikWAM")
        name: Nome human-readable della voce (es. "Rachel")
        category: Categoria della voce (es. "premade", "cloned")
        labels: Dizionario di metadati aggiuntivi (es. {"accent": "american"})
    """

    voice_id: str
    name: str
    category: str | None = None
    labels: dict[str, str] | None = None

    def __str__(self) -> str:
        """Rappresentazione human-readable per CLI."""
        base = f"{self.name} ({self.voice_id})"
        if self.category:
            base += f" [{self.category}]"
        return base


@dataclass(frozen=True)
class TTSRequest:
    """Richiesta di conversione text-to-speech.

    Attributes:
        text: Testo da convertire in audio
        voice_id: ID della voce da utilizzare
        output_path: Percorso dove salvare l'audio generato
    """

    text: str
    voice_id: str
    output_path: str

    def __post_init__(self) -> None:
        """Validazione basic dei parametri."""
        if not self.text.strip():
            raise ValueError("Text cannot be empty")
        if not self.voice_id.strip():
            raise ValueError("Voice ID cannot be empty")
        if not self.output_path.strip():
            raise ValueError("Output path cannot be empty")

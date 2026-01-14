"""Command Line Interface for ElevenLabs TTS.

Platone: Semplicità d'uso è il valore primario.
Regola: Nessuna logica business significativa qui - solo interazione utente.
"""

import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from eleven_tts_cli.adapters.elevenlabs_api import ElevenLabsClient
from eleven_tts_cli.core.errors import (
    AuthenticationError,
    ElevenLabsCLIError,
    NetworkError,
    RateLimitError,
)
from eleven_tts_cli.core.models import TTSRequest
from eleven_tts_cli.core.services import TTSService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="ElevenLabs Text-to-Speech CLI - Convert text to audio using ElevenLabs API"
)
console = Console()


def select_voice_interactive(service: TTSService) -> str | None:
    """Selezione voce interattiva con supporto ricerca testuale.

    Dewey: Conseguenze pratiche - UX flessibile con lista numerata + ricerca.

    Args:
        service: TTSService per recuperare e filtrare voci.

    Returns:
        Voice ID selezionato, o None se utente annulla.
    """
    console.print("\n[bold cyan]Fetching available voices...[/bold cyan]")

    try:
        all_voices = service.list_voices()
    except ElevenLabsCLIError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return None

    if not all_voices:
        console.print("[yellow]No voices available.[/yellow]")
        return None

    current_voices = all_voices

    while True:
        # Mostra tabella voci
        console.print()
        table = Table(title="Available Voices")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Name", style="green")
        table.add_column("Voice ID", style="dim")
        table.add_column("Category", style="yellow")

        for idx, voice in enumerate(current_voices, start=1):
            table.add_row(
                str(idx),
                voice.name,
                voice.voice_id,
                voice.category or "N/A",
            )

        console.print(table)

        # Input utente
        console.print(
            "\n[dim]Enter number to select, text to search, or 'q' to quit[/dim]"
        )
        user_input = input("Your choice: ").strip()

        if user_input.lower() == "q":
            return None

        # Prova interpretare come numero
        if user_input.isdigit():
            idx = int(user_input)
            if 1 <= idx <= len(current_voices):
                selected = current_voices[idx - 1]
                console.print(
                    f"[green]✓[/green] Selected: {selected.name} ({selected.voice_id})"
                )
                return selected.voice_id
            else:
                console.print(
                    f"[red]Invalid number. Please enter 1-{len(current_voices)}[/red]"
                )
                continue

        # Altrimenti interpreta come query testuale
        current_voices = service.search_voices(user_input, all_voices)

        if not current_voices:
            console.print(
                f"[yellow]No voices match '{user_input}'. Showing all voices again.[/yellow]"
            )
            current_voices = all_voices
        else:
            console.print(f"[dim]Filtered to {len(current_voices)} voice(s)[/dim]")


def get_text_input() -> str | None:
    """Chiede testo all'utente.

    Returns:
        Testo inserito o None se annullato.
    """
    console.print("\n[bold cyan]Enter the text to convert to speech:[/bold cyan]")
    console.print("[dim](Press Ctrl+D or Ctrl+C to cancel)[/dim]")

    try:
        text = input("> ").strip()
        if not text:
            console.print("[yellow]Text cannot be empty.[/yellow]")
            return None
        return text
    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]Cancelled.[/yellow]")
        return None


def get_output_filename() -> str | None:
    """Chiede nome file output all'utente.

    Returns:
        Percorso file output o None se annullato.
    """
    console.print("\n[bold cyan]Enter output filename:[/bold cyan]")
    console.print("[dim](e.g., 'output.mp3' - file will be saved in current directory)[/dim]")

    try:
        filename = input("> ").strip()
        if not filename:
            console.print("[yellow]Filename cannot be empty.[/yellow]")
            return None

        # Assicura estensione .mp3
        if not filename.lower().endswith(".mp3"):
            filename += ".mp3"

        # Costruisci path assoluto in current working directory
        output_path = Path.cwd() / filename

        return str(output_path)

    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]Cancelled.[/yellow]")
        return None


def execute_tts_with_retry(service: TTSService, request: TTSRequest) -> bool:
    """Esegue TTS con logica di retry su errore.

    Dewey: Conseguenza pratica - UX robusta con gestione errori e retry.

    Args:
        service: TTSService per generazione audio.
        request: Richiesta TTS.

    Returns:
        True se successo, False se fallito definitivamente.
    """
    while True:
        try:
            console.print("\n[bold cyan]Generating audio...[/bold cyan]")
            service.generate_audio(request)
            console.print(f"[bold green]✓ Audio saved to:[/bold green] {request.output_path}")
            return True

        except AuthenticationError as e:
            console.print(f"[bold red]Authentication Error:[/bold red] {e}")
            console.print("[yellow]Please check your ELEVENLABS_API_KEY[/yellow]")
            return False

        except RateLimitError as e:
            console.print(f"[bold red]Rate Limit Error:[/bold red] {e}")
            if not _ask_retry():
                return False

        except NetworkError as e:
            console.print(f"[bold red]Network Error:[/bold red] {e}")
            if not _ask_retry():
                return False

        except ElevenLabsCLIError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if not _ask_retry():
                return False


def _ask_retry() -> bool:
    """Chiede all'utente se vuole riprovare.

    Returns:
        True se utente vuole riprovare, False altrimenti.
    """
    console.print("\n[yellow]Do you want to retry?[/yellow] (y/n): ", end="")
    try:
        response = input().strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


@app.command()
def main(
    text: str | None = typer.Option(
        None,
        "--text",
        "-t",
        help="Text to convert to speech (if not provided, will ask interactively)",
    ),
    voice_id: str | None = typer.Option(
        None,
        "--voice-id",
        "-v",
        help="ElevenLabs voice ID (if not provided, will ask interactively)",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output filename (if not provided, will ask interactively)",
    ),
) -> None:
    """ElevenLabs TTS CLI - Convert text to speech.

    Hegel: Sintesi - modalità diretta (flag) + interattiva (prompt) coesistono.

    Examples:
        # Interactive mode
        $ python -m eleven_tts_cli

        # Direct mode
        $ python -m eleven_tts_cli --text "Hello" --voice-id "21m00..." --output audio.mp3

        # Hybrid mode
        $ python -m eleven_tts_cli --text "Hello"  # will ask for voice and output
    """
    console.print("[bold blue]ElevenLabs TTS CLI[/bold blue]\n")

    # Inizializza client e service
    try:
        client = ElevenLabsClient()
        service = TTSService(client)
    except AuthenticationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("\n[yellow]Please set ELEVENLABS_API_KEY environment variable:[/yellow]")
        console.print("  export ELEVENLABS_API_KEY='your-api-key-here'")
        sys.exit(1)

    # Modalità ibrida: chiedi interattivamente i parametri mancanti
    if not voice_id:
        voice_id = select_voice_interactive(service)
        if not voice_id:
            console.print("[yellow]Voice selection cancelled.[/yellow]")
            sys.exit(0)

    if not text:
        text = get_text_input()
        if not text:
            console.print("[yellow]Text input cancelled.[/yellow]")
            sys.exit(0)

    if not output:
        output = get_output_filename()
        if not output:
            console.print("[yellow]Output filename cancelled.[/yellow]")
            sys.exit(0)

    # Crea richiesta TTS
    try:
        request = TTSRequest(text=text, voice_id=voice_id, output_path=output)
    except ValueError as e:
        console.print(f"[bold red]Validation Error:[/bold red] {e}")
        sys.exit(1)

    # Esegui TTS con retry
    success = execute_tts_with_retry(service, request)

    if success:
        console.print("\n[bold green]✓ Done![/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]✗ Failed.[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    app()

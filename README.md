# ElevenLabs TTS CLI

Command-line tool for converting text to speech using the ElevenLabs API.

## Features

- **Interactive mode**: User-friendly prompts guide you through the process
- **Direct mode**: Pass all parameters via CLI flags for automation
- **Voice selection**: Browse available voices with search/filter capability
- **Flexible UX**: Mix and match interactive and direct modes
- **Robust error handling**: Clear error messages with retry option
- **Streaming audio**: Efficient chunk-by-chunk file writing

## Requirements

- Python 3.11 or higher
- ElevenLabs API key ([Get one here](https://elevenlabs.io/))

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd testBaseAudioElevenlabs
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install the package

```bash
pip install -e .
```

For development (includes testing and linting tools):

```bash
pip install -e ".[dev]"
```

## Configuration

Set your ElevenLabs API key as an environment variable:

```bash
export ELEVENLABS_API_KEY='your-api-key-here'
```

To make it persistent, add it to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
echo 'export ELEVENLABS_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Usage

### Interactive Mode (Recommended for first-time users)

Run without any arguments and follow the prompts:

```bash
python -m eleven_tts_cli
```

Or using the installed command:

```bash
eleven-tts
```

**Workflow:**
1. Browse and select a voice (search by name or select by number)
2. Enter the text you want to convert
3. Choose an output filename
4. Audio file is generated in the current directory

### Direct Mode (For automation/scripting)

Pass all parameters via CLI flags:

```bash
python -m eleven_tts_cli \
  --text "Hello, world!" \
  --voice-id "21m00Tcm4TlvDq8ikWAM" \
  --output hello.mp3
```

### Hybrid Mode

Mix flags and interactive prompts. Any missing parameter will be asked interactively:

```bash
# Provide text, but select voice and filename interactively
python -m eleven_tts_cli --text "Hello, world!"

# Provide voice, but enter text and filename interactively
python -m eleven_tts_cli --voice-id "21m00Tcm4TlvDq8ikWAM"
```

## Examples

### Example 1: Generate speech with default voice

```bash
python -m eleven_tts_cli \
  --text "Welcome to ElevenLabs TTS" \
  --voice-id "21m00Tcm4TlvDq8ikWAM" \
  --output welcome.mp3
```

### Example 2: Interactive voice selection

```bash
python -m eleven_tts_cli --text "Test audio"
# Will show voice list and ask for selection interactively
```

### Example 3: Search for a voice

When running in interactive mode:
1. List of all voices is shown
2. Type text (e.g., "rachel") to filter voices
3. Type number to select filtered voice
4. Type 'q' to quit

## Project Structure

```
.
├── README.md
├── agent2.md                  # Project specification
├── pyproject.toml            # Dependencies and build config
├── .gitignore
├── src/
│   └── eleven_tts_cli/
│       ├── __init__.py
│       ├── cli.py            # CLI interface (Typer)
│       ├── core/             # Business logic
│       │   ├── __init__.py
│       │   ├── models.py     # Domain models
│       │   ├── services.py   # TTS service
│       │   └── errors.py     # Custom exceptions
│       └── adapters/         # External integrations
│           ├── __init__.py
│           └── elevenlabs_api.py  # ElevenLabs API client
└── tests/
    ├── test_services.py
    └── test_cli_smoke.py
```

## Troubleshooting

### "ELEVENLABS_API_KEY not found"

**Problem**: API key not set or not accessible.

**Solution**:
```bash
export ELEVENLABS_API_KEY='your-actual-api-key'
```

Verify it's set:
```bash
echo $ELEVENLABS_API_KEY
```

### "Authentication Error: Invalid API key"

**Problem**: API key is incorrect or expired.

**Solution**:
1. Go to [ElevenLabs Dashboard](https://elevenlabs.io/)
2. Generate a new API key
3. Update your environment variable

### "Rate Limit Error"

**Problem**: Too many requests to the API.

**Solution**:
- Wait a few minutes before retrying
- Check your ElevenLabs plan limits
- The CLI will ask if you want to retry automatically

### "Network Error"

**Problem**: No internet connection or ElevenLabs API is down.

**Solution**:
- Check your internet connection
- Visit [ElevenLabs Status Page](https://status.elevenlabs.io/)
- The CLI will ask if you want to retry

### Audio file not generated

**Problem**: File permissions or disk space issues.

**Solution**:
- Ensure you have write permissions in the current directory
- Check available disk space
- Try specifying a different output directory

## Development

### Setup development environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=eleven_tts_cli --cov-report=html
```

### Code quality

**Linting** (ruff):
```bash
ruff check src/
```

**Formatting** (black):
```bash
black src/ tests/
```

**Type checking** (mypy):
```bash
mypy src/
```

### Run all checks

```bash
ruff check src/ && black --check src/ tests/ && mypy src/ && pytest
```

## Architecture Principles

This project follows a **clean architecture** pattern:

- **`core/`**: Pure business logic, no I/O dependencies
- **`adapters/`**: External integrations (HTTP, file system)
- **`cli.py`**: User interaction layer

**Design values** (in priority order):
1. Simplicity of use
2. Robustness
3. Maintainability
4. Transparency
5. Security

See `agent2.md` for detailed design philosophy and methodology.

## License

MIT License (or specify your license)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all checks pass (`ruff`, `black`, `mypy`, `pytest`)
5. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check [ElevenLabs API Documentation](https://docs.elevenlabs.io/)

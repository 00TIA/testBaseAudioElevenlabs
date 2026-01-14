"""Unit tests for TTSService."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from eleven_tts_cli.core.errors import FileSystemError
from eleven_tts_cli.core.models import TTSRequest, Voice
from eleven_tts_cli.core.services import TTSService


@pytest.fixture
def mock_api_client():
    """Mock ElevenLabsClient for testing."""
    return Mock()


@pytest.fixture
def service(mock_api_client):
    """TTSService instance with mocked client."""
    return TTSService(mock_api_client)


@pytest.fixture
def sample_voices():
    """Sample voice data for testing."""
    return [
        Voice(voice_id="voice-3", name="Charlie", category="premade"),
        Voice(voice_id="voice-1", name="Alice", category="premade"),
        Voice(voice_id="voice-2", name="Bob", category="cloned"),
    ]


def test_list_voices_returns_sorted_list(service, mock_api_client, sample_voices):
    """Test that list_voices returns voices sorted alphabetically."""
    mock_api_client.get_voices.return_value = sample_voices

    result = service.list_voices()

    assert len(result) == 3
    assert result[0].name == "Alice"
    assert result[1].name == "Bob"
    assert result[2].name == "Charlie"
    mock_api_client.get_voices.assert_called_once()


def test_list_voices_empty_list(service, mock_api_client):
    """Test list_voices with no available voices."""
    mock_api_client.get_voices.return_value = []

    result = service.list_voices()

    assert result == []


def test_search_voices_by_name(service, sample_voices):
    """Test searching voices by name."""
    result = service.search_voices("alice", sample_voices)

    assert len(result) == 1
    assert result[0].name == "Alice"


def test_search_voices_case_insensitive(service, sample_voices):
    """Test that search is case-insensitive."""
    result = service.search_voices("CHARLIE", sample_voices)

    assert len(result) == 1
    assert result[0].name == "Charlie"


def test_search_voices_partial_match(service, sample_voices):
    """Test partial string matching."""
    result = service.search_voices("ob", sample_voices)

    assert len(result) == 1
    assert result[0].name == "Bob"


def test_search_voices_by_id(service, sample_voices):
    """Test searching by voice ID."""
    result = service.search_voices("voice-2", sample_voices)

    assert len(result) == 1
    assert result[0].name == "Bob"


def test_search_voices_no_match(service, sample_voices):
    """Test search with no matching results."""
    result = service.search_voices("nonexistent", sample_voices)

    assert result == []


def test_search_voices_empty_query(service, sample_voices):
    """Test search with empty query returns all voices."""
    result = service.search_voices("", sample_voices)

    assert len(result) == 3


def test_generate_audio_success(service, mock_api_client):
    """Test successful audio generation and file writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = str(Path(tmpdir) / "output.mp3")
        request = TTSRequest(
            text="Hello world",
            voice_id="voice-1",
            output_path=output_path,
        )

        # Mock streaming response
        mock_api_client.text_to_speech_stream.return_value = iter(
            [
                b"chunk1",
                b"chunk2",
                b"chunk3",
            ]
        )

        service.generate_audio(request)

        # Verify file was created
        assert Path(output_path).exists()

        # Verify content
        with open(output_path, "rb") as f:
            content = f.read()
            assert content == b"chunk1chunk2chunk3"

        # Verify API was called correctly
        mock_api_client.text_to_speech_stream.assert_called_once_with(
            text="Hello world",
            voice_id="voice-1",
        )


def test_generate_audio_directory_not_exists(service, mock_api_client):
    """Test error when output directory doesn't exist."""
    request = TTSRequest(
        text="Hello",
        voice_id="voice-1",
        output_path="/nonexistent/directory/file.mp3",
    )

    with pytest.raises(FileSystemError, match="Output directory does not exist"):
        service.generate_audio(request)


def test_generate_audio_output_is_directory(service, mock_api_client):
    """Test error when output path is a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        request = TTSRequest(
            text="Hello",
            voice_id="voice-1",
            output_path=tmpdir,  # Directory, not file
        )

        with pytest.raises(FileSystemError, match="not a file"):
            service.generate_audio(request)


def test_tts_request_validation_empty_text():
    """Test TTSRequest validation rejects empty text."""
    with pytest.raises(ValueError, match="Text cannot be empty"):
        TTSRequest(text="", voice_id="voice-1", output_path="out.mp3")


def test_tts_request_validation_empty_voice_id():
    """Test TTSRequest validation rejects empty voice ID."""
    with pytest.raises(ValueError, match="Voice ID cannot be empty"):
        TTSRequest(text="Hello", voice_id="", output_path="out.mp3")


def test_tts_request_validation_empty_output():
    """Test TTSRequest validation rejects empty output path."""
    with pytest.raises(ValueError, match="Output path cannot be empty"):
        TTSRequest(text="Hello", voice_id="voice-1", output_path="")

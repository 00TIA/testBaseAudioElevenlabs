"""Smoke tests for CLI interface.

These tests verify basic CLI functionality without making real API calls.
"""

import os
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from eleven_tts_cli.cli import app
from eleven_tts_cli.core.models import Voice

runner = CliRunner()


@pytest.fixture
def mock_env_api_key(monkeypatch):
    """Set mock API key in environment."""
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-api-key-12345")


@pytest.fixture
def sample_voices():
    """Sample voices for testing."""
    return [
        Voice(voice_id="voice-1", name="Alice", category="premade"),
        Voice(voice_id="voice-2", name="Bob", category="premade"),
    ]


def test_cli_missing_api_key():
    """Test CLI exits with error when API key is missing."""
    # Ensure env var is not set
    with patch.dict(os.environ, {}, clear=True):
        result = runner.invoke(app, [])

        assert result.exit_code == 1
        assert "ELEVENLABS_API_KEY" in result.stdout


@patch("eleven_tts_cli.cli.ElevenLabsClient")
@patch("eleven_tts_cli.cli.TTSService")
def test_cli_direct_mode_success(
    mock_service_class,
    mock_client_class,
    mock_env_api_key,
    tmp_path,
):
    """Test CLI in direct mode with all parameters provided."""
    output_file = tmp_path / "output.mp3"

    # Mock service
    mock_service = Mock()
    mock_service_class.return_value = mock_service
    mock_service.generate_audio.return_value = None

    # Create empty file to simulate successful generation
    output_file.touch()

    result = runner.invoke(
        app,
        [
            "--text",
            "Hello world",
            "--voice-id",
            "voice-1",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Done" in result.stdout or "saved" in result.stdout.lower()


@patch("eleven_tts_cli.cli.ElevenLabsClient")
def test_cli_help_message(mock_client_class):
    """Test that CLI shows help message."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "ElevenLabs" in result.stdout
    assert "text" in result.stdout.lower()
    assert "voice" in result.stdout.lower()


@patch("eleven_tts_cli.cli.ElevenLabsClient")
@patch("eleven_tts_cli.cli.TTSService")
def test_cli_handles_authentication_error(
    mock_service_class,
    mock_client_class,
    mock_env_api_key,
):
    """Test CLI handles authentication errors gracefully."""
    from eleven_tts_cli.core.errors import AuthenticationError

    # Mock client to raise auth error
    mock_client_class.side_effect = AuthenticationError("Invalid API key")

    result = runner.invoke(app, [])

    assert result.exit_code == 1
    assert "Error" in result.stdout or "error" in result.stdout.lower()


def test_voice_model_string_representation():
    """Test Voice model __str__ method."""
    voice = Voice(
        voice_id="test-123",
        name="Test Voice",
        category="premade",
    )

    result = str(voice)

    assert "Test Voice" in result
    assert "test-123" in result
    assert "premade" in result

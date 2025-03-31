# test_voices.py
import pytest
from unittest.mock import MagicMock, patch
from core.cat.plugins.voices.voices import agent_prompt_prefix, before_cat_sends_message, has_cyrillic


@pytest.mark.parametrize("text, expected", [
    ("Hello", False),
    ("Привет", True),
    ("Hello and Привет", True),
    ("12345", False),
    ("", False),
])
def test_has_cyrillic(text, expected):
    assert has_cyrillic(text) == expected

@patch('core.cat.plugins.voices.voices.ElevenLabs')
@patch('core.cat.plugins.voices.voices.open')
def test_process_success(mock_open, mock_elevenlabs):
    # Mock settings
    settings_mock = MagicMock()
    settings_mock.get.side_effect = lambda key: {
        "eleven_lab_voice_id": "test_voice_id",
        "eleven_lab_apikey": "dummy_api_key"
    }[key]

    # Mock the cat.mad_hatter.get_plugin().load_settings()
    mock_cat = MagicMock()
    mock_cat.mad_hatter.get_plugin.return_value.load_settings.return_value = settings_mock

    # Mock ElevenLabs client
    mock_client = MagicMock()
    mock_elevenlabs.return_value = mock_client
    mock_client.text_to_speech.convert.return_value = [b'audio_bytes']

    filename = "test.wav"
    text = "Hello"

    _process(text, filename, mock_cat)

    mock_elevenlabs.assert_called_once_with(api_key="dummy_api_key")
    mock_client.text_to_speech.convert.assert_called_once()
    mock_open.assert_called_once_with(filename, 'wb')
    mock_open().write.assert_called_once_with(b'audio_bytes')

@patch('core.cat.plugins.voices.voices.cat')
def test_agent_prompt_prefix(mock_cat):
    mock_settings = {"eleven_lab_system_prompt": "This is a test prompt."}
    mock_cat.mad_hatter.get_plugin().load_settings.return_value = mock_settings

    prefix = agent_prompt_prefix("original_prefix", mock_cat)

    assert prefix == "This is a test prompt."

def test_before_cat_sends_message():
    from datetime import datetime

    mock_cat = MagicMock()
    mock_cat.mad_hatter.get_plugin().load_settings.return_value = {
        "eleven_lab_system_prompt": "dummy_prompt",
        "eleven_lab_voice_id": "dummy_id"
    }

    final_output = {"content": "Hello"}
    formatted_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_path = "admin/assets/voice"
    expected_filename = f"{folder_path}/voice_{formatted_datetime}.wav"

    with patch('os.makedirs') as mock_makedirs, patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False  # Simulate folder not existing

        result = before_cat_sends_message(final_output, mock_cat)

        mock_makedirs.assert_called_once_with(folder_path)
        assert result == final_output

def inc(x):
    return x + 1

def test_answer():
    assert inc(3) == 4

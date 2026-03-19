import pytest
from unittest.mock import patch, MagicMock
from src.main import call_ollama

@patch("requests.post")
def test_call_ollama_success(mock_post):
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Análisis IA"}
    mock_post.return_value = mock_response

    result = call_ollama("test-model", "test-prompt")
    
    assert result == "Análisis IA"
    mock_post.assert_called_once()

@patch("requests.post")
@patch("time.sleep", return_value=None) # Skip sleep during tests
def test_call_ollama_retry_success(mock_sleep, mock_post):
    # Setup mock: 1 failure then 1 success
    fail_response = MagicMock()
    fail_response.raise_for_status.side_effect = Exception("Temp Error")
    
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {"response": "Éxito tras reintento"}
    
    mock_post.side_effect = [fail_response, success_response]

    result = call_ollama("test-model", "test-prompt")
    
    assert result == "Éxito tras reintento"
    assert mock_post.call_count == 2

@patch("requests.post")
@patch("time.sleep", return_value=None)
def test_call_ollama_total_failure(mock_sleep, mock_post):
    # Setup mock: always fails
    fail_response = MagicMock()
    fail_response.raise_for_status.side_effect = Exception("Fatal Error")
    mock_post.return_value = fail_response

    with pytest.raises(Exception):
        call_ollama("test-model", "test-prompt")
    
    assert mock_post.call_count == 3 # Default MAX_RETRIES
